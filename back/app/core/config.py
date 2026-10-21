"""Validated configuration loaded once for the selected deployment environment."""

import os
from functools import lru_cache
from ipaddress import ip_network
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from app.core.origins import canonical_origin

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Foodify API"
    debug: bool = False
    docs_enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1, le=32)
    database_url: str = Field(repr=False)
    migration_database_url: str | None = Field(default=None, repr=False)
    mysql_host: str | None = None
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_database: str = "foodify"
    mysql_user: str = "foodify"
    mysql_password: SecretStr | None = None
    mysql_migration_password: SecretStr | None = None
    redis_host: str | None = None
    redis_password: SecretStr | None = None
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    redis_url: str = Field(repr=False)
    jwt_secret: SecretStr
    email_encryption_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "foodify-api"
    jwt_audience: str = "foodify-client"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    verification_token_minutes: int = Field(default=60, ge=5, le=1440)
    reset_token_minutes: int = Field(default=15, ge=5, le=60)
    oauth_state_minutes: int = Field(default=10, ge=1, le=15)
    public_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    browser_cookie_same_site: Literal["lax", "strict", "none"] = "lax"
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    trusted_proxy_ips: list[str] = Field(default_factory=list)
    max_request_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    smtp_host: str = "localhost"
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: EmailStr = "noreply@foodify.example.com"
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = Field(default=10, ge=1, le=60)
    oauth_google_client_id: str | None = None
    oauth_google_client_secret: SecretStr | None = None
    oauth_google_redirect_uri: str | None = None
    oauth_facebook_client_id: str | None = None
    oauth_facebook_client_secret: SecretStr | None = None
    oauth_facebook_redirect_uri: str | None = None
    oauth_facebook_graph_version: str = "v26.0"
    frontend_proxy_secret: SecretStr | None = None

    @model_validator(mode="before")
    @classmethod
    def assemble_hosted_connection_urls(cls, values: dict) -> dict:
        def secret_value(value: str | SecretStr) -> str:
            return value.get_secret_value() if isinstance(value, SecretStr) else value

        if not values.get("database_url") and values.get("mysql_host") and values.get("mysql_password"):
            connection = URL.create(
                "mysql+pymysql", username=values.get("mysql_user", "foodify"),
                password=secret_value(values["mysql_password"]), host=values["mysql_host"],
                port=int(values.get("mysql_port", 3306)), database=values.get("mysql_database", "foodify"),
                query={"charset": "utf8mb4"},
            )
            values["database_url"] = connection.render_as_string(hide_password=False)
            if not values.get("migration_database_url") and values.get("mysql_migration_password"):
                values["migration_database_url"] = connection.set(
                    username="foodify_migrator", password=secret_value(values["mysql_migration_password"]),
                ).render_as_string(hide_password=False)
        if not values.get("redis_url") and values.get("redis_host") and values.get("redis_password"):
            values["redis_url"] = URL.create(
                "redis", username="default", password=secret_value(values["redis_password"]),
                host=values["redis_host"], port=6379, database="0",
            ).render_as_string(hide_password=False)
        return values

    @field_validator("database_url", "migration_database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            url = make_url(value)
        except (ArgumentError, ValueError):
            raise ValueError("Database connection URL is malformed.") from None
        if url.drivername != "mysql+pymysql":
            raise ValueError("Database connections must use mysql+pymysql.")
        if not url.host or not url.database or not url.username:
            raise ValueError("Database connection URL must include host, database and username.")
        return url.render_as_string(hide_password=False)

    @property
    def browser_cookie_secure(self) -> bool:
        return self.app_env == "production" or urlsplit(self.public_base_url).scheme == "https"

    @property
    def browser_allowed_origins(self) -> list[str]:
        return list(
            dict.fromkeys([*self.cors_origins, canonical_origin(self.frontend_url, allow_path=True)])
        )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        try:
            database = make_url(self.database_url)
        except (ArgumentError, ValueError):
            raise ValueError("DATABASE_URL is malformed.") from None
        if not database.host or not database.database or not database.username:
            raise ValueError("DATABASE_URL must include host, database and username.")
        if self.migration_database_url:
            migration = make_url(self.migration_database_url)
            if migration.get_backend_name() != database.get_backend_name():
                raise ValueError("Runtime and migration databases must use the same database engine.")
        redis = urlsplit(self.redis_url)
        if redis.scheme not in {"redis", "rediss"} or not redis.hostname:
            raise ValueError("REDIS_URL must be a valid Redis connection URL.")
        secret = self.jwt_secret.get_secret_value()
        if len(secret.strip().encode()) < 32 or len(set(secret)) < 8:
            raise ValueError("JWT_SECRET must contain at least 32 bytes.")
        if any(
            marker in secret.lower() for marker in ("change", "example", "development", "replace")
        ):
            raise ValueError("JWT_SECRET must be randomly generated, not an example placeholder.")
        try:
            Fernet(self.email_encryption_key.get_secret_value().encode())
        except (ValueError, TypeError) as exc:
            raise ValueError("EMAIL_ENCRYPTION_KEY must be a valid Fernet key.") from exc
        if self.smtp_use_ssl and self.smtp_use_tls:
            raise ValueError("Choose SMTP_USE_SSL or SMTP_USE_TLS, not both.")
        if self.frontend_proxy_secret and len(self.frontend_proxy_secret.get_secret_value().encode()) < 32:
            raise ValueError("FRONTEND_PROXY_SECRET must contain at least 32 bytes.")
        smtp_password = self.smtp_password.get_secret_value() if self.smtp_password else ""
        if bool(self.smtp_username) != bool(smtp_password):
            raise ValueError("SMTP username and password must be configured together.")
        for field in ("public_base_url", "frontend_url"):
            value = getattr(self, field)
            url = urlsplit(value)
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or url.query
                or url.fragment
                or url.username
            ):
                raise ValueError(
                    f"{field.upper()} must be an absolute HTTP URL without query or credentials."
                )
        if not self.trusted_hosts or "*" in self.trusted_hosts:
            raise ValueError("TRUSTED_HOSTS must list explicit host names.")
        for host in self.trusted_hosts:
            if (
                not host
                or host != host.strip()
                or "/" in host
                or ":" in host
                or ("*" in host and (not host.startswith("*.") or "*" in host[1:]))
            ):
                raise ValueError(
                    "TRUSTED_HOSTS must contain host names without schemes, ports or paths."
                )
        proxy_networks = []
        for address in self.trusted_proxy_ips:
            try:
                network = ip_network(address, strict=False)
            except ValueError:
                raise ValueError(
                    "TRUSTED_PROXY_IPS must contain IP addresses or CIDR networks."
                ) from None
            if network.prefixlen == 0:
                raise ValueError("TRUSTED_PROXY_IPS cannot trust every address.")
            proxy_networks.append(str(network))
        self.trusted_proxy_ips = proxy_networks
        for origin in self.cors_origins:
            url = urlsplit(origin)
            if (
                origin == "*"
                or url.scheme not in {"http", "https"}
                or not url.hostname
                or url.path not in {"", "/"}
                or url.query
                or url.fragment
                or url.username
            ):
                raise ValueError("CORS_ORIGINS must list explicit HTTP origins.")
        self.cors_origins = [canonical_origin(origin) for origin in self.cors_origins]
        if self.browser_cookie_same_site == "none" and not self.browser_cookie_secure:
            raise ValueError("BROWSER_COOKIE_SAME_SITE=none requires an HTTPS PUBLIC_BASE_URL.")
        for provider in ("google", "facebook"):
            values = [
                getattr(self, f"oauth_{provider}_{suffix}")
                for suffix in ("client_id", "client_secret", "redirect_uri")
            ]
            configured = [
                bool(value.get_secret_value().strip())
                if isinstance(value, SecretStr)
                else bool(value)
                for value in values
            ]
            if any(configured) and not all(configured):
                raise ValueError(f"Configure all three {provider.upper()} OAuth settings together.")
            if values[2]:
                url = urlsplit(values[2])
                if (
                    url.scheme not in {"http", "https"}
                    or not url.hostname
                    or url.query
                    or url.fragment
                    or url.username
                ):
                    raise ValueError(f"Invalid {provider.upper()} OAuth redirect URI.")
        if self.app_env == "production":
            if self.debug or self.docs_enabled:
                raise ValueError("Production requires DEBUG=false and DOCS_ENABLED=false.")
            if not database.password or database.username.lower() == "root":
                raise ValueError("Production requires a dedicated database user and password.")
            if not redis.password:
                raise ValueError("Production Redis must require a password.")
            if not (self.smtp_use_tls or self.smtp_use_ssl):
                raise ValueError("Production SMTP must use STARTTLS or implicit TLS.")
            if not self.smtp_username or not self.smtp_password:
                raise ValueError("Production SMTP requires authentication.")
            credentials = [database.password, redis.password, self.smtp_username, smtp_password]
            credentials.extend(
                value.get_secret_value()
                for value in (self.oauth_google_client_secret, self.oauth_facebook_client_secret)
                if value
            )
            if any(
                any(marker in value.lower() for marker in ("replace_with", "change_me", "changeme"))
                for value in credentials
                if value
            ):
                raise ValueError("Production credentials must not contain example placeholders.")
            if self.smtp_from_email.endswith((".local", ".example.com", "@example.com")):
                raise ValueError("Production SMTP_FROM_EMAIL must use your real domain.")
            urls = [self.public_base_url, self.frontend_url, *self.cors_origins]
            urls.extend(
                value
                for value in (self.oauth_google_redirect_uri, self.oauth_facebook_redirect_uri)
                if value
            )
            if any(urlsplit(value).scheme != "https" for value in urls):
                raise ValueError("Production public URLs and CORS origins must use HTTPS.")
            if any(host in {"localhost", "127.0.0.1", "testserver"} for host in self.trusted_hosts):
                raise ValueError("Production TRUSTED_HOSTS must use deployment host names.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development")
    if environment not in {"development", "test", "production"}:
        raise ValueError("APP_ENV must be development, test or production.")
    return Settings(_env_file=PROJECT_ROOT / f".env.{environment}", app_env=environment)
