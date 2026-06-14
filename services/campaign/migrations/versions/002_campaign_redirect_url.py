"""campaign redirect url

Revision ID: 002_redirect_url
Revises: 001_campaigns
Create Date: 2026-06-14

"""
from alembic import op
import sqlalchemy as sa

revision = "002_redirect_url"
down_revision = "001_campaigns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "campaigns",
        sa.Column("redirect_url", sa.String(length=2048), nullable=False, server_default=""),
    )
    op.alter_column("campaigns", "redirect_url", server_default=None)


def downgrade():
    op.drop_column("campaigns", "redirect_url")
