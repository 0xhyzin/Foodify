"""Only the register business use case."""

from app.infrastructure.models import User, new_id
from app.shared.errors import PersistenceConflict
from app.shared.ports import PasswordHasher, UnitOfWork
from app.shared.time import utcnow
from app.users.register.dto import RegisterRequest
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    UserRepository,
)


class RegisterService:
    def __init__(
        self,
        users: UserRepository,
        actions: ActionTokenRepository,
        hasher: PasswordHasher,
        email_actions: EmailActionServiceInterface,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.actions = actions
        self.hasher = hasher
        self.email_actions = email_actions
        self.uow = uow

    def execute(self, payload: RegisterRequest) -> None:
        # Perform the expensive hash for both existing and new addresses.
        password_hash = self.hasher.hash(payload.password)
        if self.users.get_by_email(payload.email) is not None:
            return
        user = User(
            id=new_id(),
            name=payload.name,
            email=payload.email,
            password_hash=password_hash,
            is_active=True,
            is_email_verified=False,
            created_at=utcnow(),
            roles=[self.actions.get_customer_role()],
        )
        self.users.add(user)
        try:
            self.uow.flush()
            self.email_actions.queue_email_action(user, "verify_email")
            self.uow.commit()
        except PersistenceConflict:
            # A simultaneous registration may have won the unique email key.
            self.uow.rollback()
            if self.users.get_by_email(payload.email) is None:
                raise
