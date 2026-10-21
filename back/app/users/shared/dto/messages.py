"""Common message shape for generic account-action responses."""

from app.shared.dto import APIModel


class MessageResponse(APIModel):
    message: str


GENERIC_EMAIL_MESSAGE = "If the account is eligible, an email with the next steps will be sent."
