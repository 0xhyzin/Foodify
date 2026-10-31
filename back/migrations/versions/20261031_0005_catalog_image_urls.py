"""Store catalog artwork URLs without truncating image links."""

import sqlalchemy as sa
from alembic import op

revision = "20261031_0005"
down_revision = "20261031_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("restaurants", "menu_items"):
        op.alter_column(
            table,
            "artwork",
            existing_type=sa.String(length=30),
            type_=sa.String(length=2048),
            existing_nullable=False,
            existing_server_default="burger",
        )


def downgrade() -> None:
    bind = op.get_bind()
    for table in ("restaurants", "menu_items"):
        long_urls = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table} WHERE CHAR_LENGTH(artwork) > 30")
        ).scalar_one()
        if long_urls:
            raise RuntimeError(
                f"Cannot downgrade {table}.artwork: {long_urls} catalog URL(s) "
                "would be truncated. Replace those URLs before retrying."
            )
        op.alter_column(
            table,
            "artwork",
            existing_type=sa.String(length=2048),
            type_=sa.String(length=30),
            existing_nullable=False,
            existing_server_default="burger",
        )
