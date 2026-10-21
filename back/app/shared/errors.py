"""Public application errors and HTTP exception translation."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """An expected failure safe to expose to API clients."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class PersistenceConflict(AppError):
    """A storage constraint failed; no SQL details cross the adapter boundary."""

    def __init__(self) -> None:
        super().__init__("resource_conflict", "The change conflicts with existing data.", 409)


def error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response_headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    }
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response_headers["X-Request-ID"] = request_id
    settings = getattr(request.app.state, "settings", None)
    if settings is not None and settings.app_env == "production":
        response_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers=response_headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_application_error(request: Request, exc: AppError) -> JSONResponse:
        headers = None
        if exc.status_code == 429 and isinstance(exc.details, dict):
            headers = {"Retry-After": str(exc.details.get("retry_after", 60))}
        if exc.status_code == 401:
            headers = {"WWW-Authenticate": "Bearer"}
        return error_response(request, exc.code, exc.message, exc.status_code, exc.details, headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Never echo rejected passwords, tokens, request bodies or validator contexts.
        details = [
            {"field": ".".join(map(str, error["loc"])), "type": error["type"]}
            for error in exc.errors()
        ]
        return error_response(
            request, "validation_error", "Request validation failed.", 422, details
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
        messages = {404: "Resource not found.", 405: "Method not allowed."}
        return error_response(
            request,
            "http_error",
            messages.get(exc.status_code, "Request could not be completed."),
            exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # SQLAlchemy exceptions may embed parameters: log only the exception class.
        logger.error(
            "Database failure request_id=%s type=%s",
            getattr(request.state, "request_id", None),
            type(exc).__name__,
        )
        return error_response(
            request, "service_unavailable", "Service temporarily unavailable.", 503
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unexpected failure request_id=%s type=%s",
            getattr(request.state, "request_id", None),
            type(exc).__name__,
        )
        return error_response(request, "internal_error", "An unexpected error occurred.", 500)
