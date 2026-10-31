"""Explicit, allow-listed seed of the approved demo marketplace.

Canonical fixtures live in shared/ and never pretend the brands are partners.
Stable UUIDs preserve cart/order references. Only known demo rows are updated.
Production requires both an explicit command flag and an environment opt-in.
"""

import argparse
import json
import os
from decimal import Decimal
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure import models as _identity_models  # noqa: F401
from app.infrastructure.database import get_session_factory
from app.ordering.models import BrowseCategory, MenuItem, Restaurant
from sqlalchemy import select


RETIRED_DEMO_MERCHANT_IDS = {
    "7bf40981-91d3-5b5c-867f-36bf4fb5a892",  # old burger demo
    "5323d5be-80e2-5479-be0a-e2c487a0d40a",  # old shawarma demo
    "e23da371-2e02-5e8c-8132-5b5577428437",  # old donut demo
    "643f7d7f-05ec-52d3-b002-2981be18a882",  # old grocery demo
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize the approved demo catalog.")
    parser.add_argument(
        "--allow-production",
        action="store_true",
        help="allow the fixed demo catalog to be synchronized in production",
    )
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env == "production" and not (
        args.allow_production
        and os.environ.get("FOODIFY_ALLOW_DEMO_CATALOG_SEED", "").lower() == "true"
    ):
        raise SystemExit(
            "Production catalog seeding requires --allow-production and "
            "FOODIFY_ALLOW_DEMO_CATALOG_SEED=true."
        )
    shared = Path(__file__).resolve().parents[2] / "shared"
    catalog = json.loads((shared / "demo-catalog.json").read_text())
    categories = json.loads((shared / "demo-categories.json").read_text())
    product_count = sum(len(entry["meals"]) for entry in catalog)
    current_ids = {entry["id"] for entry in catalog}
    managed_ids = current_ids | RETIRED_DEMO_MERCHANT_IDS
    with get_session_factory()() as session, session.begin():
        for merchant in session.scalars(
            select(Restaurant).where(Restaurant.id.in_(RETIRED_DEMO_MERCHANT_IDS))
        ):
            merchant.is_active = False
        for menu in session.scalars(
            select(MenuItem).where(MenuItem.restaurant_id.in_(managed_ids))
        ):
            menu.is_available = False
        tags = {}
        for entry in categories:
            category = session.get(BrowseCategory, entry["code"])
            if category is None:
                category = BrowseCategory(**entry)
                session.add(category)
            tags[category.code] = category
        session.flush()
        for entry in catalog:
            merchant = session.get(Restaurant, entry["id"])
            if merchant is None:
                merchant = Restaurant(id=entry["id"])
                session.add(merchant)
            merchant.name = entry["name"]
            merchant.slug = entry["slug"]
            merchant.kind = entry["kind"]
            merchant.category = entry["category"]
            merchant.description = entry["description"]
            merchant.logo = entry.get("logo")
            merchant.artwork = entry["photo"]
            merchant.address = "Cairo, Egypt (demo)"
            merchant.delivery_fee = Decimal(str(entry["fee"]))
            merchant.delivery_minutes = entry["minutes"]
            merchant.rating = Decimal(str(entry["score"]))
            merchant.reviews = int(entry["reviews"])
            merchant.is_active = True
            merchant.categories = [tags[code] for code in entry["tags"]]
            session.flush()
            for product in entry["meals"]:
                menu = session.get(MenuItem, product["id"])
                if menu is None:
                    menu = MenuItem(id=product["id"], restaurant_id=merchant.id)
                    session.add(menu)
                menu.name = product["name"]
                menu.category = product.get("category") or entry["tags"][0]
                menu.description = product["description"]
                menu.price = Decimal(str(product["price"]))
                menu.artwork = product["photo"]
                menu.is_available = True
    print(
        f"Demo catalog synchronized: {len(catalog)} merchants, {product_count} products, "
        f"{len(categories)} browse categories."
    )


if __name__ == "__main__":
    main()
