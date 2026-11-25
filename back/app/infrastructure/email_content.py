"""Render action-email text and HTML consistently for every delivery provider."""

from dataclasses import dataclass
from html import escape
from urllib.parse import quote


@dataclass(frozen=True)
class ActionEmailContent:
    subject: str
    text: str
    html: str


def render_action_email(frontend_url: str, purpose: str, raw_token: str) -> ActionEmailContent:
    actions = {
        "verify_email": (
            "Verify your Foodify email",
            "/verify-email",
            "verify your email address",
            "Verify email address",
        ),
        "password_reset": (
            "Reset your Foodify password",
            "/reset-password",
            "reset your password",
            "Reset password",
        ),
    }
    if purpose not in actions:
        raise ValueError("Unsupported email action.")
    subject, path, instruction, button_label = actions[purpose]
    link = f"{frontend_url.rstrip('/')}{path}#token={quote(raw_token, safe='')}"
    safe_link = escape(link, quote=True)
    safe_subject = escape(subject)
    safe_instruction = escape(instruction)
    safe_button = escape(button_label)
    html_body = (
        "<!DOCTYPE html>"
        "<html lang=\"en\">"
        "<body style=\"margin:0;padding:24px;background:#f7f7f8;font-family:Arial,sans-serif;color:#171719;\">"
        "<div style=\"max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e8e6e9;"
        "border-radius:14px;overflow:hidden;\">"
        "<div style=\"background:#d42135;padding:18px 24px;color:#ffffff;font-size:22px;font-weight:800;\">"
        "foodify"
        "</div>"
        "<div style=\"padding:24px;line-height:1.65;font-size:15px;\">"
        f"<h1 style=\"margin:0 0 12px;font-size:20px;color:#171719;\">{safe_subject}</h1>"
        f"<p style=\"margin:0 0 18px;color:#4a4850;\">Use the button below to {safe_instruction}.</p>"
        "<p style=\"margin:0 0 22px;\">"
        f"<a href=\"{safe_link}\" style=\"display:inline-block;background:#d42135;color:#ffffff;"
        "text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px;\">"
        f"{safe_button}</a></p>"
        "<p style=\"margin:0 0 8px;font-size:12px;color:#68666e;\">"
        "If the button does not open, copy this link into your browser:</p>"
        f"<p style=\"margin:0 0 16px;font-size:12px;word-break:break-all;color:#b8192a;\">{safe_link}</p>"
        "<p style=\"margin:0;font-size:12px;color:#68666e;\">"
        "If you did not request this, you can safely ignore this email. Do not share this link with anyone.</p>"
        "</div></div></body></html>"
    )
    return ActionEmailContent(
        subject=subject,
        text=(
            f"Use this link to {instruction}:\n\n{link}\n\n"
            "If you did not request this, you can ignore this email.\n"
            "Do not share this link with anyone."
        ),
        html=html_body,
    )
