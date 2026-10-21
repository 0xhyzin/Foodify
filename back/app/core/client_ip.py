"""Accept a client IP from the frontend proxy only with a fresh HMAC signature."""

import hashlib
import hmac
import time
from ipaddress import ip_address

from fastapi import Request

from app.core.config import get_settings

PROXY_SIGNATURE_MAX_AGE_SECONDS = 120

def get_client_ip(request: Request) -> str:
    fallback = request.client.host if request.client else "unknown"
    secret = get_settings().frontend_proxy_secret
    if not secret:
        return fallback
    timestamp = request.headers.get("x-foodify-proxy-time", "")
    proposed_ip = request.headers.get("x-foodify-proxy-ip", "")
    signature = request.headers.get("x-foodify-proxy-signature", "")
    if len(signature) != 64 or any(char not in "0123456789abcdef" for char in signature):
        return fallback
    try:
        if abs(time.time() - int(timestamp)) > PROXY_SIGNATURE_MAX_AGE_SECONDS:
            return fallback
        ip_address(proposed_ip)
    except ValueError:
        return fallback
    message = f"{timestamp}\n{request.method}\n{request.url.path}\n{proposed_ip}"
    expected = hmac.new(
        secret.get_secret_value().encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return proposed_ip if hmac.compare_digest(signature, expected) else fallback
