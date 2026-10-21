"""Free-host startup: prepare the database, then replace this process with Uvicorn."""

import os
import sys

from app.core.config import PROJECT_ROOT
from scripts.release import main as prepare_release


def main() -> None:
    prepare_release()
    os.execv(sys.executable, [
        sys.executable, str(PROJECT_ROOT / "run.py"),
        "--env", "production", "--host", "0.0.0.0", "--workers", "1",
    ])


if __name__ == "__main__":
    main()
