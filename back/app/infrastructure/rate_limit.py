"""Shared atomic Redis rate limits, including across API workers and instances."""

import hashlib

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings
from app.shared.errors import AppError

_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return {count, redis.call('TTL', KEYS[1])}
"""


class RedisRateLimiter:
    def __init__(self, settings: Settings) -> None:
        tls_options = (
            {"ssl_cert_reqs": "required", "ssl_check_hostname": True}
            if settings.redis_url.startswith("rediss://")
            else {}
        )
        self._client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
            health_check_interval=30,
            **tls_options,
        )
        self._environment = settings.app_env
        self._script = self._client.register_script(_LIMIT_SCRIPT)

    def check(self, scope: str, key: str, limit: int, window_seconds: int) -> None:
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate limit and window must be positive.")
        # Hash identifiers so Redis keys never contain emails, IPs or raw tokens.
        digest = hashlib.sha256(key.encode()).hexdigest()
        storage_key = f"foodify:{self._environment}:rate:{scope}:{digest}"
        try:
            count, ttl = self._script(keys=[storage_key], args=[window_seconds])
        except RedisError as exc:
            # Fail closed: loss of Redis must never silently disable abuse limits.
            raise AppError("service_unavailable", "Service temporarily unavailable.", 503) from exc
        if int(count) > limit:
            raise AppError(
                "rate_limit_exceeded",
                "Too many requests. Please try again later.",
                429,
                {"retry_after": max(int(ttl), 1)},
            )

    def close(self) -> None:
        self._client.close()
