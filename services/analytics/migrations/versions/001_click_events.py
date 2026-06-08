"""click events

Revision ID: 001_click_events
Revises:
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_click_events"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "click_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_click_events_campaign_id"), "click_events", ["campaign_id"]
    )
    op.create_index(op.f("ix_click_events_target_id"), "click_events", ["target_id"])
    op.create_index(op.f("ix_click_events_owner_id"), "click_events", ["owner_id"])
    op.create_index(op.f("ix_click_events_token"), "click_events", ["token"])
    op.create_index(
        op.f("ix_click_events_created_at"), "click_events", ["created_at"]
    )


def downgrade():
    op.drop_index(op.f("ix_click_events_created_at"), table_name="click_events")
    op.drop_index(op.f("ix_click_events_token"), table_name="click_events")
    op.drop_index(op.f("ix_click_events_owner_id"), table_name="click_events")
    op.drop_index(op.f("ix_click_events_target_id"), table_name="click_events")
    op.drop_index(op.f("ix_click_events_campaign_id"), table_name="click_events")
    op.drop_table("click_events")
