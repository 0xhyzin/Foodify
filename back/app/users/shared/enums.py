from enum import StrEnum


class TokenTypeCode(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    VERIFY_EMAIL = "verify_email"
    PASSWORD_RESET = "password_reset"


class SocialProvider(StrEnum):
    GOOGLE = "google"
    FACEBOOK = "facebook"
