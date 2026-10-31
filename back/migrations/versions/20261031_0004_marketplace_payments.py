"""Independent merchant carts, browse categories, payment lifecycle and order audit.

Preserves existing cart lines/orders. No automatic seed or external payment request.
MySQL DDL is not transactional: back up and apply in a controlled release window.
"""

import sqlalchemy as sa
from alembic import context, op

revision = "20261031_0004"
down_revision = "20261030_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "menu_items", sa.Column("artwork", sa.String(30), nullable=False, server_default="burger")
    )
    op.add_column(
        "restaurants", sa.Column("kind", sa.String(20), nullable=False, server_default="restaurant")
    )
    op.create_index("ix_restaurants_kind", "restaurants", ["kind"])
    for name, size in [("slug", 80), ("logo", 500)]:
        op.add_column("restaurants", sa.Column(name, sa.String(size), nullable=True))
    op.create_unique_constraint("uq_restaurant_slug", "restaurants", ["slug"])
    op.add_column(
        "restaurants", sa.Column("artwork", sa.String(30), nullable=False, server_default="burger")
    )
    op.create_table(
        "browse_categories",
        sa.Column("code", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("artwork", sa.String(30), nullable=False),
    )
    op.create_table(
        "restaurant_categories",
        sa.Column(
            "restaurant_id",
            sa.String(36),
            sa.ForeignKey("restaurants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "category_code",
            sa.String(40),
            sa.ForeignKey("browse_categories.code", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "favorite_restaurants",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "restaurant_id",
            sa.String(36),
            sa.ForeignKey("restaurants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # The composite index must exist before removing the index used by the user FK.
    op.create_unique_constraint("uq_cart_user_restaurant", "carts", ["user_id", "restaurant_id"])
    op.drop_index("ix_carts_user_id", "carts")
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=False)
    op.add_column("carts", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("food_orders", sa.Column("cart_id", sa.String(36), nullable=True))
    op.create_foreign_key(
        "fk_order_cart", "food_orders", "carts", ["cart_id"], ["id"], ondelete="SET NULL"
    )
    op.add_column("food_orders", sa.Column("cart_revision", sa.Integer(), nullable=True))
    for name, type_ in [
        ("provider_order_id", sa.String(80)),
        ("intention_id", sa.String(100)),
        ("checkout_token", sa.Text()),
        ("expires_at", sa.DateTime()),
        ("transaction_id", sa.String(80)),
        ("claimed_reference", sa.String(100)),
        ("verified_reference", sa.String(100)),
    ]:
        op.add_column("payments", sa.Column(name, type_, nullable=True))
    for column in ("provider_order_id", "intention_id", "transaction_id", "verified_reference"):
        op.create_unique_constraint(f"uq_payment_{column}", "payments", [column])
    op.add_column(
        "payments", sa.Column("test_mode", sa.Boolean(), nullable=False, server_default="0")
    )
    op.add_column("payments", sa.Column("transfer_recipient", sa.String(120), nullable=True))
    op.add_column("payments", sa.Column("transfer_recipient_name", sa.String(160), nullable=True))
    op.create_table(
        "order_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("food_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("note", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_order_events_order_id", "order_events", ["order_id"])
    op.execute(
        "INSERT INTO order_events (id, order_id, status, created_at) "
        "SELECT UUID(), id, status, created_at FROM food_orders"
    )
    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(36),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_id", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_payment_events_payment_id", "payment_events", ["payment_id"])


def downgrade() -> None:
    if not context.is_offline_mode():
        multiple = op.get_bind().scalar(
            sa.text(
                "SELECT COUNT(*) FROM (SELECT user_id FROM carts GROUP BY user_id "
                "HAVING COUNT(*) > 1) AS multiple_carts"
            )
        )
        real_payments = op.get_bind().scalar(
            sa.text("SELECT COUNT(*) FROM payments WHERE provider NOT IN ('sandbox', 'simulation')")
        )
        if multiple or real_payments:
            raise RuntimeError(
                "Downgrade would lose independent carts or payment audit. "
                "Export/reconcile these records first; no downgrade DDL applied."
            )
    op.drop_table("payment_events")
    op.drop_table("order_events")
    for column in ("provider_order_id", "intention_id", "transaction_id", "verified_reference"):
        op.drop_constraint(f"uq_payment_{column}", "payments", type_="unique")
    for column in (
        "provider_order_id",
        "intention_id",
        "checkout_token",
        "expires_at",
        "transaction_id",
        "claimed_reference",
        "verified_reference",
        "test_mode",
        "transfer_recipient",
        "transfer_recipient_name",
    ):
        op.drop_column("payments", column)
    op.drop_constraint("fk_order_cart", "food_orders", type_="foreignkey")
    op.drop_column("food_orders", "cart_id")
    op.drop_column("food_orders", "cart_revision")
    op.drop_column("carts", "revision")
    # Keep a usable user FK index throughout the reverse transition.
    op.create_index("uq_carts_legacy_user", "carts", ["user_id"], unique=True)
    op.drop_constraint("uq_cart_user_restaurant", "carts", type_="unique")
    op.drop_index("ix_carts_user_id", "carts")
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=True)
    op.drop_index("uq_carts_legacy_user", "carts")
    for table in ("favorite_restaurants", "restaurant_categories", "browse_categories"):
        op.drop_table(table)
    op.drop_constraint("uq_restaurant_slug", "restaurants", type_="unique")
    op.drop_index("ix_restaurants_kind", "restaurants")
    for column in ("kind", "slug", "logo", "artwork"):
        op.drop_column("restaurants", column)
    op.drop_column("menu_items", "artwork")
