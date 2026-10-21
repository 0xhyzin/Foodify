"""Create the normalized identity, RBAC and delivery-profile schema.

Revision ID: 20261020_0001
Revises: None
Create Date: 2026-10-20

This revision is intentionally explicit. Editing ORM models later does not
change historical schema definitions. MySQL DDL is not transactional; back up
the deployment before applying a revision to an existing installation.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261020_0001"
down_revision = None
branch_labels = None
depends_on = None

TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "token_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_token_types_code"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254, collation="utf8mb4_bin"), nullable=False),
        sa.Column("phone", sa.String(16), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("default_address_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_roles_user", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_user_roles_role", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_role_permissions_role", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_role_permissions_permission",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "addresses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("recipient_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("area", sa.String(100), nullable=False),
        sa.Column("street", sa.String(200), nullable=False),
        sa.Column("building", sa.String(50), nullable=False),
        sa.Column("floor", sa.String(30), nullable=True),
        sa.Column("apartment", sa.String(30), nullable=True),
        sa.Column("delivery_notes", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90", name="ck_address_latitude"
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="ck_address_longitude"
        ),
        sa.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_address_coordinates",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_addresses_user", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_addresses_user_created", "addresses", ["user_id", "created_at"])
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_auth_sessions_user", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_auth_sessions_user_expires", "auth_sessions", ["user_id", "expires_at"])
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["auth_sessions.id"],
            name="fk_refresh_tokens_session",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_refresh_tokens_session", "refresh_tokens", ["session_id"])
    op.create_table(
        "action_tokens",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("token_type_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_action_tokens_user", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["token_type_id"], ["token_types.id"], name="fk_action_tokens_type", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_action_tokens_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_action_tokens_user_type", "action_tokens", ["user_id", "token_type_id"])
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("provider_subject", sa.String(255, collation="utf8mb4_bin"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_social_accounts_user", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_social_provider_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_social_user_provider"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "oauth_states",
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("code_verifier", sa.String(128), nullable=False),
        sa.Column("nonce", sa.String(128), nullable=False),
        sa.Column("binding_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("state_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_oauth_states_expires_at", "oauth_states", ["expires_at"])
    op.create_table(
        "oauth_tickets",
        sa.Column("ticket_hash", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("binding_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_oauth_tickets_user", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("ticket_hash"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_oauth_tickets_expires_at", "oauth_tickets", ["expires_at"])
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_email_outbox_pending", "email_outbox", ["sent_at", "next_attempt_at"])
    op.create_foreign_key(
        "fk_users_default_address",
        "users",
        "addresses",
        ["default_address_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_default_address", "users", type_="foreignkey")
    op.drop_table("email_outbox")
    op.drop_table("oauth_tickets")
    op.drop_table("oauth_states")
    op.drop_table("social_accounts")
    op.drop_table("action_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("auth_sessions")
    op.drop_table("addresses")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("token_types")
    op.drop_table("permissions")
    op.drop_table("roles")
