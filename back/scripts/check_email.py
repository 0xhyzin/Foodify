"""Diagnose email configuration and optionally send a safe test verification message."""

from __future__ import annotations

import argparse
import os
import secrets

from app.core.config import get_settings
from app.infrastructure.email_sender import create_email_sender

FREE_WEBMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com"}


def inspect_configuration() -> list[str]:
    settings = get_settings()
    from_email = str(settings.smtp_from_email)
    sender_domain = from_email.rsplit("@", 1)[-1].lower()
    host_lower = settings.smtp_host.lower()
    is_local = host_lower in {"localhost", "127.0.0.1", "mailpit"}
    is_google = host_lower.endswith(("gmail.com", "googlemail.com"))

    issues: list[str] = []
    if settings.email_provider == "smtp":
        if sender_domain in FREE_WEBMAIL_DOMAINS and not (is_local or is_google):
            issues.append(
                f"DMARC alignment risk: sending from '{sender_domain}' via third-party relay "
                f"'{settings.smtp_host}'. Use SMTP_HOST=smtp.gmail.com + Google App Password, "
                "or verify your own custom domain with your relay provider."
            )
        if settings.app_env == "production" and not (settings.smtp_use_tls or settings.smtp_use_ssl):
            issues.append("Production SMTP requires TLS or SSL.")
    elif settings.email_provider == "brevo" and not settings.brevo_api_key:
        issues.append("EMAIL_PROVIDER=brevo requires BREVO_API_KEY.")
    elif settings.email_provider == "resend" and not settings.resend_api_key:
        issues.append("EMAIL_PROVIDER=resend requires RESEND_API_KEY.")

    print(
        f"app_env={settings.app_env} provider={settings.email_provider} "
        f"smtp_host={settings.smtp_host}:{settings.smtp_port} "
        f"tls={settings.smtp_use_tls} ssl={settings.smtp_use_ssl} "
        f"sender_domain={sender_domain} embedded_worker={settings.embedded_email_worker}"
    )
    if issues:
        for warning in issues:
            print(f"WARNING: {warning}")
    else:
        print("OK: Email configuration checks passed.")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and test Foodify email delivery")
    parser.add_argument(
        "--env",
        choices=("development", "test", "production"),
        default=os.getenv("APP_ENV", "development"),
    )
    parser.add_argument("--check", action="store_true", help="Inspect settings only")
    parser.add_argument("--to", help="Send a test verification email to this address")
    args = parser.parse_args()
    os.environ["APP_ENV"] = args.env

    issues = inspect_configuration()
    if args.to and not args.check:
        settings = get_settings()
        create_email_sender(settings).send_action_email(
            args.to, "verify_email", f"diag-{secrets.token_urlsafe(12)}"
        )
        print("Test verification email dispatched via active adapter.")
    elif issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
