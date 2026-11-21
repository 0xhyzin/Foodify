"""Export real FastAPI contracts without loading secrets or starting services."""

import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "back"))


def export() -> None:
    from cryptography.fernet import Fernet

    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="mysql+pymysql://docs:unused@127.0.0.1:1/foodify_docs",
        redis_url="redis://127.0.0.1:1/15",
        jwt_secret="offline-documentation-secret-only-2026",
        email_encryption_key=Fernet.generate_key().decode(),
        embedded_email_worker=False,
    )
    # openapi() inspects registered routes and DTOs. No lifespan or database
    # engine is started, and network access is explicitly blocked as a guard.
    with patch("app.main.get_settings", return_value=settings), patch.object(
        socket.socket, "connect", side_effect=RuntimeError("Documentation export is offline.")
    ):
        schema = create_app().openapi()
    destination = ROOT / "docs" / "teams" / "assets" / "openapi.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported {len(schema['paths'])} OpenAPI paths to {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    export()
