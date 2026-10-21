"""Render action-email text consistently for every delivery provider."""

from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class ActionEmailContent:
    subject: str
    text: str


def render_action_email(frontend_url: str, purpose: str, raw_token: str) -> ActionEmailContent:
    actions = {
        "verify_email": ("Verify your Foodify email", "/verify-email", "verify your email address"),
        "password_reset": ("Reset your Foodify password", "/reset-password", "reset your password"),
    }
    if purpose not in actions:
        raise ValueError("Unsupported email action.")
    subject, path, instruction = actions[purpose]
    link = f"{frontend_url.rstrip('/')}{path}#token={quote(raw_token, safe='')}"
    return ActionEmailContent(
        subject=subject,
        text=(
            f"Use this link to {instruction}:\n\n{link}\n\n"
            "If you did not request this, you can ignore this email.\n"
            "Do not share this link with anyone."
        ),
    )
