"""Sprint 3 restaurant staff scoping, delivery assignments, notifications, and order status migration."""

import sqlalchemy as sa
from alembic import op

revision = "20261121_0006"
down_revision = "20261031_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurant_staff",
        sa.Column(
            "restaurant_id",
            sa.String(36),
            sa.ForeignKey("restaurants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_restaurant_staff_user_id", "restaurant_staff", ["user_id"])

    op.create_table(
        "delivery_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("food_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "delivery_person_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "previous_delivery_person_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_by_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="assigned"),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("order_id", name="uq_delivery_assignment_order"),
    )
    op.create_index(
        "ix_delivery_assignments_order_id", "delivery_assignments", ["order_id"], unique=True
    )
    op.create_index(
        "ix_delivery_assignments_delivery_person_id",
        "delivery_assignments",
        ["delivery_person_id"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "recipient_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("food_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False, server_default="in_app"),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("delivery_status", sa.String(20), nullable=False, server_default="sent"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_order_id", "notifications", ["order_id"])
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
    op.create_index(
        "ix_notifications_recipient_read_created",
        "notifications",
        ["recipient_id", "read_at", "created_at"],
    )

    op.add_column("food_orders", sa.Column("assigned_preparer_id", sa.String(36), nullable=True))
    op.create_foreign_key(
        "fk_food_orders_assigned_preparer",
        "food_orders",
        "users",
        ["assigned_preparer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_food_orders_assigned_preparer_id",
        "food_orders",
        ["assigned_preparer_id"],
    )

    for old, new in (
        ("placed", "pending"),
        ("ready", "ready_for_pickup"),
        ("out_for_delivery", "picked_up"),
    ):
        op.execute(
            sa.text("UPDATE food_orders SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )
        op.execute(
            sa.text("UPDATE order_events SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )


def downgrade() -> None:
    for old, new in (
        ("pending", "placed"),
        ("ready_for_pickup", "ready"),
        ("picked_up", "out_for_delivery"),
    ):
        op.execute(
            sa.text("UPDATE food_orders SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )
        op.execute(
            sa.text("UPDATE order_events SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )

    op.drop_constraint("fk_food_orders_assigned_preparer", "food_orders", type_="foreignkey")
    op.drop_index("ix_food_orders_assigned_preparer_id", table_name="food_orders")
    op.drop_column("food_orders", "assigned_preparer_id")

    op.drop_index("ix_notifications_recipient_read_created", table_name="notifications")
    op.drop_index("ix_notifications_event_type", table_name="notifications")
    op.drop_index("ix_notifications_order_id", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_delivery_assignments_delivery_person_id", table_name="delivery_assignments")
    op.drop_index("ix_delivery_assignments_order_id", table_name="delivery_assignments")
    op.drop_table("delivery_assignments")

    op.drop_index("ix_restaurant_staff_user_id", table_name="restaurant_staff")
    op.drop_table("restaurant_staff")
