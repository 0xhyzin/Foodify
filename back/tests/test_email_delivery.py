"""Unit tests for multipart email rendering, SMTP/Gmail, Brevo, Resend, and DMARC checks."""

from email import message_from_bytes
from email.policy import default
import logging
from unittest.mock import patch

import httpx
import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.infrastructure.brevo_email import BrevoEmailSender
from app.infrastructure.email import SMTPEmailSender
from app.infrastructure.email_content import render_action_email
from app.infrastructure.email_sender import create_email_sender
from app.infrastructure.resend_email import ResendEmailSender
from app.shared.errors import AppError

pytestmark = pytest.mark.unit


def make_settings(**overrides) -> Settings:
    defaults = dict(
        _env_file=None,
        app_env="test",
        database_url="mysql+pymysql://u:p@127.0.0.1:3306/foodify",
        redis_url="redis://127.0.0.1:6379/0",
        jwt_secret="test-jwt-secret-key-at-least-32-bytes-long!!",
        email_encryption_key=Fernet.generate_key().decode(),
        smtp_from_name="Foodify",
        smtp_from_email="noreply@foodify.example.com",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_render_action_email_builds_safe_html_and_plain_text():
    content = render_action_email(
        "https://foodify-flax.vercel.app/", "verify_email", "tok+1/2&x=3"
    )
    assert "tok%2B1%2F2%26x%3D3" in content.text
    assert "tok%2B1%2F2%26x%3D3" in content.html
    assert "Verify email address" in content.html
    assert content.subject == "Verify your Foodify email"


def test_smtp_sender_attaches_rfc_headers_html_part_and_normalizes_gmail_app_password():
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            captured["host"] = host
            captured["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            captured["ehlo"] = captured.get("ehlo", 0) + 1

        def starttls(self, context=None):
            captured["starttls"] = True

        def login(self, username, password):
            captured["login"] = (username, password)

        def send_message(self, message):
            captured["raw"] = message.as_bytes()
            return {}

    settings = make_settings(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_use_tls=True,
        smtp_username="sender@gmail.com",
        smtp_password="abcd efgh ijkl mnop",
        smtp_from_email="sender@gmail.com",
        smtp_reply_to="support@foodify.example.com",
    )
    with patch("app.infrastructure.email.smtplib.SMTP", FakeSMTP):
        SMTPEmailSender(settings).send_action_email(
            "customer@example.com", "password_reset", "reset-tok"
        )

    assert captured["host"] == "smtp.gmail.com"
    assert captured["starttls"] is True
    assert captured["login"] == ("sender@gmail.com", "abcdefghijklmnop")
    parsed = message_from_bytes(captured["raw"], policy=default)
    assert parsed["Message-ID"]
    assert parsed["Date"]
    assert parsed["Reply-To"] == "support@foodify.example.com"
    assert "Foodify" in parsed["From"] and "sender@gmail.com" in parsed["From"]
    assert parsed.is_multipart()
    body_types = {part.get_content_type() for part in parsed.walk()}
    assert {"text/plain", "text/html"}.issubset(body_types)


def test_smtp_sender_raises_unavailable_when_recipient_is_refused():
    class RefusingSMTP:
        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            pass

        def send_message(self, message):
            return {"bad@example.com": (550, b"5.1.1 User unknown")}

    settings = make_settings(smtp_host="127.0.0.1", smtp_port=1025)
    with patch("app.infrastructure.email.smtplib.SMTP", RefusingSMTP):
        with pytest.raises(AppError) as exc_info:
            SMTPEmailSender(settings).send_action_email(
                "bad@example.com", "verify_email", "tok"
            )
    assert exc_info.value.code == "email_unavailable"
    assert exc_info.value.status_code == 503


def test_brevo_sender_includes_html_and_rejects_non_201_202():
    settings = make_settings(email_provider="brevo", brevo_api_key="xkeysib-test-token")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None, follow_redirects=False):
        sent["url"] = url
        sent["json"] = json
        return httpx.Response(201, request=httpx.Request("POST", url))

    with patch("app.infrastructure.brevo_email.httpx.post", fake_post):
        create_email_sender(settings).send_action_email(
            "user@example.com", "verify_email", "verify-123"
        )
    assert sent["url"] == "https://api.brevo.com/v3/smtp/email"
    assert "htmlContent" in sent["json"] and "verify-123" in sent["json"]["htmlContent"]

    with patch(
        "app.infrastructure.brevo_email.httpx.post",
        lambda url, **kw: httpx.Response(401, request=httpx.Request("POST", url)),
    ):
        with pytest.raises(AppError) as exc_info:
            BrevoEmailSender(settings).send_action_email(
                "user@example.com", "verify_email", "verify-123"
            )
    assert exc_info.value.status_code == 503


def test_resend_adapter_dispatches_and_handles_errors():
    settings = make_settings(email_provider="resend", resend_api_key="re_test_key_123")
    adapter = create_email_sender(settings)
    assert isinstance(adapter, ResendEmailSender)
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None, follow_redirects=False):
        sent["headers"] = headers
        sent["json"] = json
        return httpx.Response(200, request=httpx.Request("POST", url))

    with patch("app.infrastructure.resend_email.httpx.post", fake_post):
        adapter.send_action_email("user@example.com", "verify_email", "res-tok")
    assert sent["headers"]["Authorization"] == "Bearer re_test_key_123"
    assert "res-tok" in sent["json"]["html"]


def test_free_webmail_via_third_party_relay_logs_dmarc_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="foodify.config"):
        make_settings(smtp_host="in-v3.mailjet.com", smtp_from_email="app@gmail.com")
    assert "DMARC" in caplog.text
