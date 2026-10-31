"""Small ASGI boundary for body limits, request IDs and response hardening."""

import re
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings

_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class JsonTrustedHostMiddleware(TrustedHostMiddleware):
    """Keep Starlette's host parser and return the API error envelope on rejection."""

    def __init__(self, app: ASGIApp, allowed_hosts: list[str]) -> None:
        self._validated_app = app
        super().__init__(self._forward_valid_host, allowed_hosts=allowed_hosts, www_redirect=False)

    async def _forward_valid_host(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["foodify.host_validated"] = True
        await self._validated_app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._validated_app(scope, receive, send)
            return

        async def envelope_rejection(message: Message) -> None:
            if scope.get("foodify.host_validated"):
                await send(message)
            elif message["type"] == "http.response.start":
                response = JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "invalid_host",
                            "message": "The request host is not allowed.",
                            "details": None,
                            "request_id": scope.get("state", {}).get("request_id"),
                        }
                    },
                )
                await response(scope, receive, send)

        await super().__call__(scope, receive, envelope_rejection)


class SecurityMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming_headers = Headers(scope=scope)
        proposed_id = incoming_headers.get("x-request-id", "")
        request_id = proposed_id if _REQUEST_ID.fullmatch(proposed_id) else str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                headers["Cache-Control"] = "no-store"
                headers["Pragma"] = "no-cache"
                if self.settings.docs_enabled and scope["path"] in {
                    "/docs",
                    "/redoc",
                    "/docs/oauth2-redirect",
                }:
                    headers["Content-Security-Policy"] = (
                        "default-src 'self'; base-uri 'self'; object-src 'none'; "
                        "form-action 'self'; frame-ancestors 'none'; "
                        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "img-src 'self' data: https://fastapi.tiangolo.com; "
                        "font-src 'self' https://fonts.gstatic.com"
                    )
                else:
                    headers["Content-Security-Policy"] = (
                        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                    )
                if self.settings.app_env == "production":
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            await send(message)

        async def reject_body(status: int, code: str, message: str) -> None:
            response = JSONResponse(
                status_code=status,
                content={
                    "error": {
                        "code": code,
                        "message": message,
                        "details": None,
                        "request_id": request_id,
                    }
                },
            )
            await response(scope, receive, secured_send)

        declared_length = incoming_headers.get("content-length")
        if declared_length is not None:
            try:
                size = int(declared_length)
            except ValueError:
                await reject_body(400, "invalid_content_length", "Invalid Content-Length header.")
                return
            if size < 0:
                await reject_body(400, "invalid_content_length", "Invalid Content-Length header.")
                return
            if size > self.settings.max_request_bytes:
                await reject_body(
                    413, "request_too_large", "Request body exceeds the allowed size."
                )
                return

        # Bound streamed/chunked uploads before the JSON parser allocates memory.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if len(body) > self.settings.max_request_bytes:
                await reject_body(
                    413, "request_too_large", "Request body exceeds the allowed size."
                )
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def buffered_receive() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, buffered_receive, secured_send)
