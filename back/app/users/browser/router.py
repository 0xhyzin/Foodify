"""Assemble protected cookie transports; business rules remain in their feature slices."""

from fastapi import APIRouter, Depends

from app.users.browser.login.router import router as login_router
from app.users.browser.logout.router import router as logout_router
from app.users.browser.oauth_complete.router import router as oauth_complete_router
from app.users.browser.refresh_session.router import router as refresh_router
from app.users.browser.shared.dependencies import require_browser_client

router = APIRouter(prefix="/browser", dependencies=[Depends(require_browser_client)])
router.include_router(login_router)
router.include_router(refresh_router)
router.include_router(oauth_complete_router)
router.include_router(logout_router)
