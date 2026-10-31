"""Harden Sprint 2 while preserving the incoming revision 0002.

Revision ID: 20261030_0003
Revises: 20261030_0002

Existing development payments from revision 0002 are explicitly marked simulated.
No live payment provider existed in that revision. MySQL DDL is not transactional;
back up first and run during a controlled release window.
"""

import sqlalchemy as sa
from alembic import context, op

revision = "20261030_0003"
down_revision = "20261030_0002"
branch_labels = None
depends_on = None


def replace_foreign_key(
    table: str, column: str, target: str, name: str, ondelete: str, nullable: bool | None = None
) -> None:
    """Revision 0002 left FK names to MySQL. Resolve them in both offline and online SQL."""
    op.execute(
        sa.text(
            "SET @foodify_fk = (SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() "
            f"AND TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}' "
            "AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1)"
        )
    )
    op.execute(
        sa.text(
            f"SET @foodify_ddl = CONCAT('ALTER TABLE `{table}` DROP FOREIGN KEY `', "
            "@foodify_fk, '`')"
        )
    )
    op.execute("PREPARE foodify_stmt FROM @foodify_ddl")
    op.execute("EXECUTE foodify_stmt")
    op.execute("DEALLOCATE PREPARE foodify_stmt")
    if nullable is not None:
        op.alter_column(table, column, existing_type=sa.String(36), nullable=nullable)
    op.create_foreign_key(name, table, target, [column], ["id"], ondelete=ondelete)


def upgrade() -> None:
    # Validate legacy rows before the first non-transactional DDL operation.
    if not context.is_offline_mode():
        invalid_queries = (
            "SELECT COUNT(*) FROM restaurants WHERE rating NOT BETWEEN 0 AND 5 "
            "OR reviews < 0 OR delivery_minutes < 0",
            "SELECT COUNT(*) FROM cart_items WHERE quantity NOT BETWEEN 1 AND 99",
            "SELECT COUNT(*) FROM food_order_items WHERE quantity NOT BETWEEN 1 AND 99",
            "SELECT COUNT(*) FROM food_orders WHERE subtotal < 0 OR delivery_fee < 0 "
            "OR total <> subtotal + delivery_fee",
            "SELECT COUNT(*) FROM payments WHERE amount < 0",
        )
        if any(op.get_bind().scalar(sa.text(query)) for query in invalid_queries):
            raise RuntimeError(
                "Legacy ordering data violates the new constraints. "
                "Review it before applying revision 0003; no 0003 DDL was applied."
            )
    op.add_column(
        "restaurants",
        sa.Column("delivery_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    for expression, name in [
        ("rating BETWEEN 0 AND 5", "ck_restaurant_rating"),
        ("reviews >= 0", "ck_restaurant_reviews"),
        ("delivery_minutes >= 0", "ck_restaurant_delivery_minutes"),
        ("delivery_fee >= 0", "ck_restaurant_delivery_fee"),
    ]:
        op.create_check_constraint(name, "restaurants", expression)
    op.create_check_constraint("ck_cart_item_max_quantity", "cart_items", "quantity <= 99")
    op.create_check_constraint("ck_order_item_max_quantity", "food_order_items", "quantity <= 99")

    op.add_column("food_orders", sa.Column("delivery_address", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE food_orders AS o JOIN addresses AS a ON a.id = o.address_id
        SET o.delivery_address = JSON_OBJECT(
            'label', a.label, 'recipient_name', a.recipient_name, 'phone', a.phone,
            'country_code', a.country_code, 'city', a.city, 'area', a.area,
            'street', a.street, 'building', a.building, 'floor', a.floor,
            'apartment', a.apartment, 'delivery_notes', a.delivery_notes,
            'latitude', a.latitude, 'longitude', a.longitude)
    """)
    op.alter_column("food_orders", "delivery_address", existing_type=sa.JSON(), nullable=False)
    # Dropping/recreating by discovered names also works for MySQL-generated names.
    replace_foreign_key("food_orders", "user_id", "users", "fk_food_orders_user", "RESTRICT")
    replace_foreign_key(
        "food_orders",
        "address_id",
        "addresses",
        "fk_food_orders_address",
        "SET NULL",
        nullable=True,
    )
    op.add_column("food_orders", sa.Column("checkout_key", sa.String(36), nullable=True))
    op.add_column("food_orders", sa.Column("checkout_fingerprint", sa.String(64), nullable=True))
    op.add_column(
        "food_orders", sa.Column("currency", sa.String(3), nullable=False, server_default="EGP")
    )
    op.create_unique_constraint(
        "uq_order_user_checkout_key", "food_orders", ["user_id", "checkout_key"]
    )
    op.create_index(
        "ix_food_orders_restaurant_created", "food_orders", ["restaurant_id", "created_at"]
    )
    for column in ("subtotal", "delivery_fee", "total"):
        op.alter_column(
            "food_orders",
            column,
            existing_type=sa.Numeric(10, 2),
            type_=sa.Numeric(12, 2),
            existing_nullable=False,
        )
    op.create_check_constraint(
        "ck_order_amounts", "food_orders", "subtotal >= 0 AND delivery_fee >= 0"
    )
    op.create_check_constraint("ck_order_total", "food_orders", "total = subtotal + delivery_fee")
    # Payment is the single source of payment status; the API derives it for the order view.
    op.drop_column("food_orders", "payment_status")
    op.alter_column(
        "payments",
        "amount",
        existing_type=sa.Numeric(10, 2),
        type_=sa.Numeric(12, 2),
        existing_nullable=False,
    )
    op.create_check_constraint("ck_payment_amount", "payments", "amount >= 0")
    op.execute(
        "UPDATE payments SET provider = 'simulation', status = 'simulated' "
        "WHERE provider = 'sandbox'"
    )


def downgrade() -> None:
    # The old schema cannot represent orders whose saved address was deleted.
    if not context.is_offline_mode():
        missing = op.get_bind().scalar(
            sa.text("SELECT COUNT(*) FROM food_orders WHERE address_id IS NULL")
        )
        large_totals = op.get_bind().scalar(
            sa.text(
                "SELECT COUNT(*) FROM food_orders WHERE subtotal > 99999999.99 "
                "OR delivery_fee > 99999999.99 OR total > 99999999.99"
            )
        )
        large_payments = op.get_bind().scalar(
            sa.text("SELECT COUNT(*) FROM payments WHERE amount > 99999999.99")
        )
        if missing or large_totals or large_payments:
            raise RuntimeError(
                "Cannot downgrade: old schema cannot represent deleted addresses or larger totals."
            )
    op.add_column(
        "food_orders",
        sa.Column("payment_status", sa.String(30), nullable=False, server_default="paid"),
    )
    op.execute(
        "UPDATE food_orders o JOIN payments p ON p.order_id = o.id SET o.payment_status = p.status"
    )
    op.drop_constraint("ck_payment_amount", "payments", type_="check")
    op.alter_column(
        "payments",
        "amount",
        existing_type=sa.Numeric(12, 2),
        type_=sa.Numeric(10, 2),
        existing_nullable=False,
    )
    op.drop_constraint("ck_order_total", "food_orders", type_="check")
    op.drop_constraint("ck_order_amounts", "food_orders", type_="check")
    for column in ("subtotal", "delivery_fee", "total"):
        op.alter_column(
            "food_orders",
            column,
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
        )
    op.drop_index("ix_food_orders_restaurant_created", "food_orders")
    op.drop_constraint("uq_order_user_checkout_key", "food_orders", type_="unique")
    for column in ("currency", "checkout_fingerprint", "checkout_key", "delivery_address"):
        op.drop_column("food_orders", column)
    replace_foreign_key(
        "food_orders",
        "address_id",
        "addresses",
        "fk_food_orders_address",
        "RESTRICT",
        nullable=False,
    )
    replace_foreign_key("food_orders", "user_id", "users", "fk_food_orders_user", "CASCADE")
    op.drop_constraint("ck_order_item_max_quantity", "food_order_items", type_="check")
    op.drop_constraint("ck_cart_item_max_quantity", "cart_items", type_="check")
    for name in (
        "ck_restaurant_rating",
        "ck_restaurant_reviews",
        "ck_restaurant_delivery_minutes",
        "ck_restaurant_delivery_fee",
    ):
        op.drop_constraint(name, "restaurants", type_="check")
    op.drop_column("restaurants", "delivery_fee")
