"""Canonical HTTP origins shared by CORS and the browser CSRF boundary."""

from urllib.parse import urlsplit


def canonical_origin(value: str, *, allow_path: bool = False) -> str:
    url = urlsplit(value)
    if (
        value != value.strip()
        or url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or (not allow_path and url.path not in {"", "/"})
    ):
        raise ValueError("An explicit HTTP origin is required.")
    hostname = url.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    port = url.port
    default_port = 443 if url.scheme == "https" else 80
    suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{url.scheme}://{hostname}{suffix}"
