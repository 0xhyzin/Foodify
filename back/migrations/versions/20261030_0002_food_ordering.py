"""Restaurant catalog, carts, orders and simulated payment records.

Revision ID: 20261030_0002
Revises: 20261020_0001
"""
import sqlalchemy as sa
from alembic import op

revision = "20261030_0002"
down_revision = "20261020_0001"
branch_labels = None
depends_on = None

TABLE_OPTIONS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"}

def upgrade():
    op.create_table("restaurants",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("address", sa.String(300), nullable=False), sa.Column("image", sa.String(500)),
        sa.Column("rating", sa.Numeric(3,2), nullable=False, server_default="0"),
        sa.Column("reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivery_minutes", sa.Integer(), nullable=False, server_default="35"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False), **TABLE_OPTIONS)
    op.create_index("ix_restaurants_name", "restaurants", ["name"]); op.create_index("ix_restaurants_category", "restaurants", ["category"]); op.create_index("ix_restaurants_is_active", "restaurants", ["is_active"])
    op.create_table("menu_items",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("restaurant_id", sa.String(36), sa.ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("category", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(10,2), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("image", sa.String(500)), sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("price >= 0", name="ck_menu_item_price"), **TABLE_OPTIONS)
    op.create_index("ix_menu_items_restaurant_id", "menu_items", ["restaurant_id"]); op.create_index("ix_menu_items_category", "menu_items", ["category"]); op.create_index("ix_menu_items_is_available", "menu_items", ["is_available"]); op.create_index("ix_menu_restaurant_category", "menu_items", ["restaurant_id", "category"])
    op.create_table("carts", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("restaurant_id", sa.String(36), sa.ForeignKey("restaurants.id", ondelete="SET NULL")), sa.Column("updated_at", sa.DateTime(), nullable=False), **TABLE_OPTIONS)
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=True)
    op.create_table("cart_items", sa.Column("id", sa.String(36), primary_key=True), sa.Column("cart_id", sa.String(36), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False), sa.Column("menu_item_id", sa.String(36), sa.ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.CheckConstraint("quantity > 0", name="ck_cart_item_quantity"), sa.UniqueConstraint("cart_id", "menu_item_id", name="uq_cart_menu_item"), **TABLE_OPTIONS)
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_table("food_orders", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("restaurant_id", sa.String(36), sa.ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False), sa.Column("address_id", sa.String(36), sa.ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("payment_method", sa.String(30), nullable=False), sa.Column("payment_status", sa.String(30), nullable=False), sa.Column("subtotal", sa.Numeric(10,2), nullable=False), sa.Column("delivery_fee", sa.Numeric(10,2), nullable=False), sa.Column("total", sa.Numeric(10,2), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), **TABLE_OPTIONS)
    op.create_index("ix_food_orders_user_id", "food_orders", ["user_id"]); op.create_index("ix_food_orders_status", "food_orders", ["status"]); op.create_index("ix_food_orders_user_created", "food_orders", ["user_id", "created_at"])
    op.create_table("food_order_items", sa.Column("id", sa.String(36), primary_key=True), sa.Column("order_id", sa.String(36), sa.ForeignKey("food_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("menu_item_id", sa.String(36), sa.ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False), sa.Column("item_name", sa.String(160), nullable=False), sa.Column("unit_price", sa.Numeric(10,2), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.CheckConstraint("quantity > 0", name="ck_order_item_quantity"), sa.CheckConstraint("unit_price >= 0", name="ck_order_item_price"), **TABLE_OPTIONS)
    op.create_index("ix_food_order_items_order_id", "food_order_items", ["order_id"])
    op.create_table("payments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("order_id", sa.String(36), sa.ForeignKey("food_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("provider", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("amount", sa.Numeric(10,2), nullable=False), sa.Column("reference", sa.String(80), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("order_id"), sa.UniqueConstraint("reference"), **TABLE_OPTIONS)
    op.create_index("ix_payments_order_id", "payments", ["order_id"], unique=True)

def downgrade():
    op.drop_table("payments"); op.drop_table("food_order_items"); op.drop_table("food_orders"); op.drop_table("cart_items"); op.drop_table("carts"); op.drop_table("menu_items"); op.drop_table("restaurants")
