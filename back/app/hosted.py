"""FastAPI Cloud entrypoint; local development continues to use ``run.py``."""

from app.main import create_app

app = create_app()
