"""Opaque secrets and their one-way lookup digests; independent of JWT/HTTP."""

import hashlib
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_browser_binding_verifier(verifier: str) -> str:
    """Hash the browser binding verifier using the same challenge as the web app."""
    challenge = hashlib.sha256(verifier.encode("ascii")).hexdigest()
    return hash_token(challenge)
