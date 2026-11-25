"""Idempotently bootstrap one verified account per Foodify portal (@foodify.app only)."""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass

from sqlalchemy import select

from app.infrastructure.database import get_session_factory
from app.infrastructure.models import Address, Role, User
from app.ordering.models import Restaurant, RestaurantStaff
from app.shared.time import utcnow
from app.users.shared.dependencies import get_password_hasher


@dataclass(frozen=True, slots=True)
class PortalSeedSpec:
    portal: str
    email: str
    name: str
    roles: tuple[str, ...]
    phone: str | None = None
    link_restaurants: bool = False
    seed_address: bool = False


PORTAL_ACCOUNTS: tuple[PortalSeedSpec, ...] = (
    PortalSeedSpec(
        portal="admin",
        email="admin@foodify.app",
        name="إدارة المنصة — Foodify",
        roles=("admin",),
    ),
    PortalSeedSpec(
        portal="operations",
        email="manager@foodify.app",
        name="مدير المطاعم والعمليات",
        roles=("operations_manager", "restaurant_manager"),
        link_restaurants=True,
    ),
    PortalSeedSpec(
        portal="kitchen",
        email="kitchen@foodify.app",
        name="مسؤول المطبخ وتحضير الطلبات",
        roles=("order_preparer",),
        link_restaurants=True,
    ),
    PortalSeedSpec(
        portal="delivery",
        email="courier@foodify.app",
        name="مندوب التوصيل — بورسعيد",
        roles=("courier",),
        phone="+201009998877",
    ),
    PortalSeedSpec(
        portal="customer",
        email="customer@foodify.app",
        name="عميل تجريبي — بورسعيد",
        roles=("customer",),
        phone="+201001112233",
        seed_address=True,
    ),
)


def bootstrap_portal_accounts(password: str | None = None) -> dict[str, object]:
    """Create or sync @foodify.app portal accounts without touching existing real users."""
    raw_password = password or os.environ.get("FOODIFY_BOOTSTRAP_PASSWORD") or (
        f"Foodify!{secrets.token_urlsafe(12)}"
    )
    if len(raw_password) < 15:
        raise ValueError("Bootstrap password must be at least 15 characters long.")

    password_hash = get_password_hasher().hash(raw_password)
    factory = get_session_factory()
    created_or_updated: list[dict[str, object]] = []

    with factory() as session:
        role_map = {role.code: role for role in session.scalars(select(Role))}
        active_restaurants = list(
            session.scalars(select(Restaurant).where(Restaurant.is_active.is_(True)))
        )

        for spec in PORTAL_ACCOUNTS:
            if not spec.email.endswith("@foodify.app"):
                raise RuntimeError("Refusing to mutate non-@foodify.app user.")
            roles = [role_map[code] for code in spec.roles]
            user = session.scalar(select(User).where(User.email == spec.email))
            if user is None:
                user = User(
                    name=spec.name,
                    email=spec.email,
                    phone=spec.phone,
                    password_hash=password_hash,
                    is_email_verified=True,
                    is_active=True,
                    created_at=utcnow(),
                    roles=roles,
                )
                session.add(user)
                session.flush()
            else:
                user.name = spec.name
                user.password_hash = password_hash
                user.is_email_verified = True
                user.is_active = True
                if spec.phone:
                    user.phone = spec.phone
                user.roles = roles
                session.flush()

            if spec.link_restaurants:
                existing_rest_ids = set(
                    session.scalars(
                        select(RestaurantStaff.restaurant_id).where(
                            RestaurantStaff.user_id == user.id
                        )
                    )
                )
                for rest in active_restaurants:
                    if rest.id not in existing_rest_ids:
                        session.add(
                            RestaurantStaff(
                                restaurant_id=rest.id,
                                user_id=user.id,
                                created_at=utcnow(),
                            )
                        )

            if spec.seed_address and user.default_address_id is None:
                existing_addr = session.scalar(
                    select(Address).where(Address.user_id == user.id)
                )
                if existing_addr is None:
                    existing_addr = Address(
                        user_id=user.id,
                        label="المنزل",
                        recipient_name=spec.name,
                        phone=spec.phone or "+201001112233",
                        country_code="EG",
                        city="Port Said",
                        area="Al-Sharq",
                        street="طرح البحر",
                        building="10",
                        floor="2",
                        apartment="4",
                        delivery_notes="أمام ممشى بورسعيد السياحي",
                        created_at=utcnow(),
                    )
                    session.add(existing_addr)
                    session.flush()
                user.default_address_id = existing_addr.id

            created_or_updated.append(
                {
                    "portal": spec.portal,
                    "email": spec.email,
                    "roles": list(spec.roles),
                }
            )
        session.commit()

    return {"password": raw_password, "accounts": created_or_updated}


if __name__ == "__main__":
    result = bootstrap_portal_accounts()
    out_path = os.environ.get("BOOTSTRAP_OUTPUT_FILE")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(f"Bootstrapped {len(result['accounts'])} portal accounts -> {out_path}")
    else:
        print(json.dumps({"accounts": result["accounts"]}, ensure_ascii=False, indent=2))
