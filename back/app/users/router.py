"""Router assembly only; each operation owns its transport and business files."""

from fastapi import APIRouter, Depends

from app.dependencies import limit_auth_requests
from app.users.addresses.add_address.router import router as add_address_router
from app.users.addresses.delete_address.router import router as delete_address_router
from app.users.addresses.list_addresses.router import router as list_addresses_router
from app.users.addresses.set_default_address.router import router as set_default_address_router
from app.users.addresses.update_address.router import router as update_address_router
from app.users.browser.router import router as browser_session_router
from app.users.forgot_password.router import router as forgot_password_router
from app.users.get_profile.router import router as get_profile_router
from app.users.login.router import router as login_router
from app.users.logout.router import router as logout_router
from app.users.logout_all.router import router as logout_all_router
from app.users.oauth.callback.router import router as oauth_callback_router
from app.users.oauth.complete.router import router as oauth_complete_router
from app.users.oauth.start.router import router as oauth_start_router
from app.users.refresh_session.router import router as refresh_session_router
from app.users.register.router import router as register_router
from app.users.resend_verification.router import router as resend_verification_router
from app.users.reset_password.router import router as reset_password_router
from app.users.update_profile.router import router as update_profile_router
from app.users.verify_email.router import router as verify_email_router

auth_router = APIRouter(
    prefix="/auth", tags=["Authentication"], dependencies=[Depends(limit_auth_requests)]
)
router = APIRouter(prefix="/users", tags=["Customer profile"])

auth_router.include_router(register_router)
auth_router.include_router(login_router)
auth_router.include_router(resend_verification_router)
auth_router.include_router(verify_email_router)
auth_router.include_router(forgot_password_router)
auth_router.include_router(reset_password_router)
auth_router.include_router(refresh_session_router)
auth_router.include_router(logout_router)
auth_router.include_router(logout_all_router)
auth_router.include_router(oauth_start_router)
auth_router.include_router(oauth_callback_router)
auth_router.include_router(oauth_complete_router)
auth_router.include_router(browser_session_router)

router.include_router(get_profile_router)
router.include_router(update_profile_router)
router.include_router(list_addresses_router)
router.include_router(add_address_router)
router.include_router(update_address_router)
router.include_router(delete_address_router)
router.include_router(set_default_address_router)
