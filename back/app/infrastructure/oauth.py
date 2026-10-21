"""Provider HTTP adapters; account creation and session policy live in auth services."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError

from app.core.config import Settings
from app.shared.errors import AppError
from app.shared.ports import OAuthIdentity


class SocialOAuthGateway:
    """Exchange authorization codes for a verified, provider-scoped identity.

    This adapter never persists provider credentials or tokens. Its caller owns
    single-use state, browser binding, nonce storage and user/account decisions.
    """

    GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
    HTTP_TIMEOUT_SECONDS = 10

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.google_signing_keys = PyJWKClient(
            self.GOOGLE_JWKS_URL,
            cache_jwk_set=True,
            cache_keys=False,
            lifespan=300,
            timeout=self.HTTP_TIMEOUT_SECONDS,
        )

    def authorization_url(self, provider: str, state: str, code_verifier: str, nonce: str) -> str:
        """Build an authorization-code URL without exposing the client secret."""
        self._require_provider_configuration(provider)
        if not state:
            raise self._authentication_failed()
        if provider == "google":
            if not nonce:
                raise self._authentication_failed()
            parameters = {
                "client_id": self.settings.oauth_google_client_id,
                "redirect_uri": self.settings.oauth_google_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": self._create_pkce_challenge(code_verifier),
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
            return f"{self.GOOGLE_AUTHORIZATION_URL}?{urlencode(parameters)}"

        parameters = {
            "client_id": self.settings.oauth_facebook_client_id,
            "redirect_uri": self.settings.oauth_facebook_redirect_uri,
            "response_type": "code",
            "scope": "email,public_profile",
            "state": state,
        }
        version = self.settings.oauth_facebook_graph_version
        return f"https://www.facebook.com/{version}/dialog/oauth?{urlencode(parameters)}"

    def exchange_identity(
        self, provider: str, code: str, code_verifier: str, nonce: str
    ) -> OAuthIdentity:
        """Return identity claims only after provider-specific validation."""
        self._require_provider_configuration(provider)
        if not code:
            raise self._authentication_failed()
        if provider == "google":
            return self._exchange_google_identity(code, code_verifier, nonce)
        return self._exchange_facebook_identity(code)

    def _exchange_google_identity(self, code: str, code_verifier: str, nonce: str) -> OAuthIdentity:
        self._create_pkce_challenge(code_verifier)
        if not nonce:
            raise self._authentication_failed()
        token_response = self._request_json(
            "POST",
            self.GOOGLE_TOKEN_URL,
            data={
                "client_id": self.settings.oauth_google_client_id,
                "client_secret": self.settings.oauth_google_client_secret.get_secret_value(),
                "redirect_uri": self.settings.oauth_google_redirect_uri,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
            },
        )
        identity_token = self._required_string(token_response, "id_token")
        try:
            signing_key = self.google_signing_keys.get_signing_key_from_jwt(identity_token)
            claims = jwt.decode(
                identity_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.oauth_google_client_id,
                issuer=self.GOOGLE_ISSUERS,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
                leeway=30,
            )
        except PyJWKClientConnectionError:
            raise self._provider_unavailable() from None
        except (PyJWTError, ValueError, TypeError):
            raise self._authentication_failed() from None

        token_nonce = claims.get("nonce")
        if not isinstance(token_nonce, str) or not hmac.compare_digest(
            token_nonce.encode("utf-8"), nonce.encode("utf-8")
        ):
            raise self._authentication_failed()
        authorized_party = claims.get("azp")
        if (
            authorized_party is not None
            and authorized_party != self.settings.oauth_google_client_id
        ):
            raise self._authentication_failed()
        if isinstance(claims.get("aud"), list) and len(claims["aud"]) > 1 and not authorized_party:
            raise self._authentication_failed()

        email = self._optional_email(claims)
        return OAuthIdentity(
            provider="google",
            subject=self._required_string(claims, "sub", maximum_length=255),
            email=email,
            email_verified=self._google_email_is_authoritative(claims, email),
            display_name=self._display_name(claims, "Google user"),
        )

    @staticmethod
    def _google_email_is_authoritative(claims: dict[str, Any], email: str | None) -> bool:
        """Third-party Google Account emails still need Foodify confirmation."""
        hosted_domain = claims.get("hd")
        return bool(
            email
            and claims.get("email_verified") is True
            and (
                email.casefold().endswith("@gmail.com")
                or (isinstance(hosted_domain, str) and hosted_domain.strip())
            )
        )

    def _exchange_facebook_identity(self, code: str) -> OAuthIdentity:
        app_id = self.settings.oauth_facebook_client_id
        app_secret = self.settings.oauth_facebook_client_secret.get_secret_value()
        graph_url = f"https://graph.facebook.com/{self.settings.oauth_facebook_graph_version}"
        token_response = self._request_json(
            "POST",
            f"{graph_url}/oauth/access_token",
            data={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": self.settings.oauth_facebook_redirect_uri,
                "code": code,
            },
        )
        access_token = self._required_string(token_response, "access_token")
        debug_response = self._request_json(
            "GET",
            f"{graph_url}/debug_token",
            params={"input_token": access_token},
            headers={"Authorization": f"Bearer {app_id}|{app_secret}"},
        )
        metadata = debug_response.get("data")
        if not isinstance(metadata, dict):
            raise self._authentication_failed()
        if (
            metadata.get("is_valid") is not True
            or metadata.get("app_id") != app_id
            or metadata.get("type") != "USER"
        ):
            raise self._authentication_failed()
        self._require_unexpired_facebook_token(metadata)
        subject = self._required_string(metadata, "user_id", maximum_length=255)
        identity = self._request_json(
            "GET",
            f"{graph_url}/me",
            params={
                "fields": "id,name,email",
                "appsecret_proof": hmac.new(
                    app_secret.encode("utf-8"), access_token.encode("utf-8"), hashlib.sha256
                ).hexdigest(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if self._required_string(identity, "id", maximum_length=255) != subject:
            raise self._authentication_failed()
        return OAuthIdentity(
            provider="facebook",
            subject=subject,
            email=self._optional_email(identity),
            email_verified=False,
            display_name=self._display_name(identity, "Facebook user"),
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Bound provider I/O and translate upstream failures into safe errors."""
        try:
            with httpx.Client(
                timeout=httpx.Timeout(self.HTTP_TIMEOUT_SECONDS, connect=5),
                follow_redirects=False,
            ) as client:
                response = client.request(method, url, data=data, params=params, headers=headers)
        except httpx.RequestError:
            raise self._provider_unavailable() from None
        if response.status_code == 429 or response.status_code >= 500:
            raise self._provider_unavailable()
        if response.status_code != 200:
            raise self._authentication_failed()
        try:
            payload = response.json()
        except ValueError:
            raise self._provider_unavailable() from None
        if not isinstance(payload, dict):
            raise self._provider_unavailable()
        if "error" in payload:
            raise self._authentication_failed()
        return payload

    def _require_provider_configuration(self, provider: str) -> None:
        if provider == "google":
            configured = (
                self.settings.oauth_google_client_id
                and self.settings.oauth_google_client_secret.get_secret_value()
                and self.settings.oauth_google_redirect_uri
            )
        elif provider == "facebook":
            configured = (
                self.settings.oauth_facebook_client_id
                and self.settings.oauth_facebook_client_secret.get_secret_value()
                and self.settings.oauth_facebook_redirect_uri
                and re.fullmatch(r"v\d+\.\d+", self.settings.oauth_facebook_graph_version)
            )
        else:
            raise self._authentication_failed()
        if not configured:
            raise AppError("oauth_unavailable", "This sign-in provider is not configured.", 503)

    @staticmethod
    def _create_pkce_challenge(code_verifier: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", code_verifier):
            raise SocialOAuthGateway._authentication_failed()
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @staticmethod
    def _required_string(
        payload: dict[str, Any], field: str, *, maximum_length: int | None = None
    ) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SocialOAuthGateway._authentication_failed()
        if maximum_length is not None and len(value) > maximum_length:
            raise SocialOAuthGateway._authentication_failed()
        return value

    @staticmethod
    def _optional_email(payload: dict[str, Any]) -> str | None:
        value = payload.get("email")
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip() or len(value) > 254:
            raise SocialOAuthGateway._authentication_failed()
        return value.strip()

    @staticmethod
    def _display_name(payload: dict[str, Any], fallback: str) -> str:
        value = payload.get("name")
        return value.strip()[:100] if isinstance(value, str) and value.strip() else fallback

    @staticmethod
    def _require_unexpired_facebook_token(metadata: dict[str, Any]) -> None:
        expires_at = metadata.get("expires_at")
        if (
            not isinstance(expires_at, int)
            or isinstance(expires_at, bool)
            or expires_at <= time.time()
        ):
            raise SocialOAuthGateway._authentication_failed()
        data_expiry = metadata.get("data_access_expires_at")
        if data_expiry is not None and (
            not isinstance(data_expiry, int)
            or isinstance(data_expiry, bool)
            or (data_expiry != 0 and data_expiry <= time.time())
        ):
            raise SocialOAuthGateway._authentication_failed()

    @staticmethod
    def _authentication_failed() -> AppError:
        return AppError(
            "oauth_failed", "Social sign-in could not be completed. Please try again.", 401
        )

    @staticmethod
    def _provider_unavailable() -> AppError:
        return AppError(
            "oauth_unavailable", "The sign-in provider is temporarily unavailable.", 503
        )
