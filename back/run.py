"""Explicit environment-aware API runner. Migrations run as a separate command."""

import argparse
import logging
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Foodify API")
    parser.add_argument(
        "--env",
        choices=("development", "test", "production"),
        default=os.getenv("APP_ENV", "development"),
    )
    parser.add_argument(
        "--reload", action="store_true", help="Reload source changes in development"
    )
    parser.add_argument("--host", help="Override HOST")
    parser.add_argument("--port", type=int, help="Override PORT")
    parser.add_argument("--workers", type=int, help="Override WORKERS")
    args = parser.parse_args()
    os.environ["APP_ENV"] = args.env
    if args.reload and args.env != "development":
        parser.error("--reload is allowed only in development.")
    if args.port is not None and not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535.")
    if args.workers is not None and not 1 <= args.workers <= 32:
        parser.error("--workers must be between 1 and 32.")

    import uvicorn

    from app.core.config import get_settings

    settings = get_settings()
    workers = args.workers or settings.workers
    if args.reload and workers != 1:
        parser.error("--reload requires a single worker.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # OAuth authorization codes and tokens must never appear in request URLs in logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=args.host or settings.host,
        port=args.port or settings.port,
        workers=workers,
        reload=args.reload,
        access_log=False,
        proxy_headers=bool(settings.trusted_proxy_ips),
        forwarded_allow_ips=",".join(settings.trusted_proxy_ips),
        server_header=False,
    )


if __name__ == "__main__":
    main()
