"""Authentication, request boundaries, error contracts and shared limiter security."""

import pytest
from sqlalchemy import select

from app.infrastructure.models import User
from conftest import PASSWORD, auth_header, register, register_and_login


@pytest.mark.integration
def test_password_uses_argon2id(client, db):
    register(client)
    stored = db.scalar(select(User)).password_hash
    assert stored.startswith("$argon2id$")
    assert PASSWORD not in stored


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic abc"}, auth_header("abc.def.ghi")])
@pytest.mark.integration
def test_profile_rejects_missing_or_invalid_bearer(client, headers):
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    assert set(response.json()["error"]) == {"code", "message", "details", "request_id"}


@pytest.mark.integration
def test_tampered_token_rejected(client):
    token = register_and_login(client)
    assert client.get("/api/v1/users/me", headers=auth_header(token[:-8] + "AAAA1234")).status_code == 401


@pytest.mark.integration
def test_token_signed_with_wrong_secret_rejected(client):
    import jwt
    forged = jwt.encode({"sub": "admin", "role": "admin"}, "incorrect-secret-never-trusted-12345", algorithm="HS256")
    assert client.get("/api/v1/users/me", headers=auth_header(forged)).status_code == 401


@pytest.mark.integration
def test_expired_token_rejected(client, settings):
    import jwt
    token = register_and_login(client)
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["exp"] = claims["iat"] - 3600
    expired = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert client.get("/api/v1/users/me", headers=auth_header(expired)).status_code == 401


@pytest.mark.parametrize("field,value", [("aud", "another-client"), ("iss", "another-issuer"), ("type", "refresh")])
@pytest.mark.integration
def test_wrong_token_context_rejected(client, settings, field, value):
    import jwt
    claims = jwt.decode(register_and_login(client), options={"verify_signature": False})
    claims[field] = value
    forged = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert client.get("/api/v1/users/me", headers=auth_header(forged)).status_code == 401


@pytest.mark.integration
def test_deactivated_account_cannot_use_existing_token(client, db):
    token = register_and_login(client)
    user = db.scalar(select(User))
    user.is_active = False
    db.commit()
    assert client.get("/api/v1/users/me", headers=auth_header(token)).status_code == 401


@pytest.mark.integration
def test_unknown_route_is_structured(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["request_id"]
    assert response.headers["x-request-id"] == response.json()["error"]["request_id"]


@pytest.mark.integration
def test_untrusted_host_rejected(client):
    assert client.get("/health/live", headers={"Host": "evil.example"}).status_code == 400


@pytest.mark.integration
def test_security_headers_are_present(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


@pytest.mark.integration
def test_disallowed_cors_origin_not_reflected(client):
    response = client.options("/api/v1/auth/browser/login", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.integration
def test_allowed_cors_supports_cookie_transport(client):
    response = client.options("/api/v1/auth/browser/login", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "X-Foodify-Client"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.unit
def test_redis_limiter_hashes_identifiers_and_sets_retry_after(settings, monkeypatch):
    from app.infrastructure.rate_limit import RedisRateLimiter
    from app.shared.errors import AppError
    from redis import Redis
    calls = []

    class FakeRedis:
        def register_script(self, script):
            def execute(*, keys, args):
                calls.append((keys, args))
                return [3, 17]
            return execute

    monkeypatch.setattr(Redis, "from_url", lambda *args, **kwargs: FakeRedis())
    limiter = RedisRateLimiter(settings)
    with pytest.raises(AppError) as raised:
        limiter.check("login", "private@example.com", 2, 60)
    assert raised.value.code == "rate_limit_exceeded"
    assert raised.value.details == {"retry_after": 17}
    assert "private@example.com" not in calls[0][0][0]
    assert calls[0][1] == [60]


@pytest.mark.unit
def test_redis_failure_fails_closed(settings, monkeypatch):
    from app.infrastructure.rate_limit import RedisRateLimiter
    from app.shared.errors import AppError
    from redis import Redis
    from redis.exceptions import ConnectionError

    class FakeRedis:
        def register_script(self, script):
            def fail(**kwargs):
                raise ConnectionError("unreachable")
            return fail

    monkeypatch.setattr(Redis, "from_url", lambda *args, **kwargs: FakeRedis())
    with pytest.raises(AppError) as raised:
        RedisRateLimiter(settings).check("login", "opaque-key", 2, 60)
    assert raised.value.code == "service_unavailable"
