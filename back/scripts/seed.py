"""Seed reference definitions without creating users or demo credentials."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.database import get_session_factory
from app.infrastructure.models import Permission, Role, TokenType
from app.roles.definitions import PERMISSION_NAMES, ROLE_NAMES, ROLE_PERMISSIONS
from app.users.shared.enums import TokenTypeCode


def seed_reference_data(session: Session) -> dict[str, int]:
    """Add missing definitions/links and update names owned by source definitions.

    Existing custom roles, permissions and role-permission links are preserved.
    This function deliberately does not commit; its caller owns the transaction.
    """
    counts = {
        "roles_created": 0,
        "permissions_created": 0,
        "role_permission_links_added": 0,
        "token_types_created": 0,
        "names_updated": 0,
    }
    permissions = {item.code: item for item in session.scalars(select(Permission))}
    for code, name in PERMISSION_NAMES.items():
        permission = permissions.get(code)
        if permission is None:
            permission = Permission(code=code, name=name)
            session.add(permission)
            permissions[code] = permission
            counts["permissions_created"] += 1
        elif permission.name != name:
            permission.name = name
            counts["names_updated"] += 1
    session.flush()

    roles = {item.code: item for item in session.scalars(select(Role))}
    for role_type, name in ROLE_NAMES.items():
        code = str(role_type)
        role = roles.get(code)
        if role is None:
            role = Role(code=code, name=name, permissions=[])
            session.add(role)
            counts["roles_created"] += 1
        elif role.name != name:
            role.name = name
            counts["names_updated"] += 1
        assigned_codes = {permission.code for permission in role.permissions}
        for permission_code in sorted(ROLE_PERMISSIONS[role_type]):
            if permission_code not in assigned_codes:
                role.permissions.append(permissions[permission_code])
                counts["role_permission_links_added"] += 1

    token_types = set(session.scalars(select(TokenType.code)))
    for token_type in TokenTypeCode:
        if str(token_type) not in token_types:
            session.add(TokenType(code=str(token_type)))
            counts["token_types_created"] += 1
    session.flush()
    return counts


def main() -> None:
    settings = get_settings()
    try:
        with get_session_factory()() as session, session.begin():
            counts = seed_reference_data(session)
    except SQLAlchemyError:
        raise SystemExit(
            "Reference data could not be seeded. Check database availability and apply migrations first."
        ) from None
    print(f"Reference data synchronized (environment={settings.app_env}).")
    for name, count in counts.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
