"""Application composition. Run with python run.py --env development."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cart.router import router as cart_router
from app.checkout.router import router as checkout_router
from app.core.api_docs import API_DESCRIPTION, configure_swagger_docs
from app.core.config import get_settings
from app.core.middleware import JsonTrustedHostMiddleware, SecurityMiddleware
from app.dependencies import get_rate_limiter, limit_api_requests
from app.infrastructure.database import check_database_readiness, get_engine
from app.infrastructure.embedded_worker import EmbeddedEmailWorker
from app.orders.router import router as orders_router
from app.payments.router import router as payments_router
from app.restaurants.router import router as restaurants_router
from app.shared.dto import ErrorResponse
from app.shared.errors import AppError, register_exception_handlers
from app.users.router import auth_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = EmbeddedEmailWorker() if get_settings().embedded_email_worker else None
    if worker:
        worker.start()
    try:
        yield
    finally:
        if worker:
            await asyncio.to_thread(worker.stop)
        get_rate_limiter().close()
        get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    # OAuth requests must never log code/token query parameters.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=API_DESCRIPTION,
        debug=False,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        responses={
            code: {"model": ErrorResponse}
            for code in (400, 401, 403, 404, 409, 413, 422, 429, 500, 503)
        },
    )
    app.state.settings = settings
    register_exception_handlers(app)
    app.add_middleware(JsonTrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.browser_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-Foodify-Client",
            "Idempotency-Key",
        ],
        expose_headers=["X-Request-ID", "Retry-After"],
    )
    app.add_middleware(SecurityMiddleware, settings=settings)
    api = APIRouter(prefix="/api/v1", dependencies=[Depends(limit_api_requests)])
    api.include_router(auth_router)
    api.include_router(users_router)
    api.include_router(restaurants_router)
    api.include_router(cart_router)
    api.include_router(orders_router)
    api.include_router(checkout_router)
    api.include_router(payments_router)
    app.include_router(api)

    @app.get("/health/live", tags=["Health"])
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", tags=["Health"])
    def readiness() -> dict[str, str]:
        try:
            check_database_readiness()
            get_rate_limiter().check("readiness", "shared", 10000, 60)
        except Exception as exc:
            raise AppError(
                "not_ready", "Service dependencies are unavailable or migrations are missing.", 503
            ) from exc
        return {"status": "ready"}

    configure_swagger_docs(app)
    return app
