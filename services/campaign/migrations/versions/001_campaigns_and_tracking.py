"""campaigns, target groups, targets, tracking

Revision ID: 001_campaigns
Revises:
Create Date: 2026-06-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_campaigns"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email_content", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_campaigns_created_by"), "campaigns", ["created_by"])

    op.create_table(
        "target_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_target_groups_campaign_id"), "target_groups", ["campaign_id"]
    )

    op.create_table(
        "targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["target_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_targets_group_id"), "targets", ["group_id"])

    op.create_table(
        "tracking_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_id"),
    )
    op.create_index(op.f("ix_tracking_links_token"), "tracking_links", ["token"], unique=True)

    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tracking_link_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tracking_link_id"], ["tracking_links.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interactions_tracking_link_id"),
        "interactions",
        ["tracking_link_id"],
    )


def downgrade():
    op.drop_index(op.f("ix_interactions_tracking_link_id"), table_name="interactions")
    op.drop_table("interactions")
    op.drop_index(op.f("ix_tracking_links_token"), table_name="tracking_links")
    op.drop_table("tracking_links")
    op.drop_index(op.f("ix_targets_group_id"), table_name="targets")
    op.drop_table("targets")
    op.drop_index(op.f("ix_target_groups_campaign_id"), table_name="target_groups")
    op.drop_table("target_groups")
    op.drop_index(op.f("ix_campaigns_created_by"), table_name="campaigns")
    op.drop_table("campaigns")
