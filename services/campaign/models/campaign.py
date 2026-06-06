import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.campaign.extensions import db


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email_content: Mapped[str] = mapped_column(db.Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    target_groups: Mapped[list["TargetGroup"]] = relationship(
        "TargetGroup",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="TargetGroup.name",
    )


class TargetGroup(db.Model):
    __tablename__ = "target_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        db.ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="target_groups")
    targets: Mapped[list["Target"]] = relationship(
        "Target",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="Target.email",
    )


class Target(db.Model):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        db.ForeignKey("target_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(db.String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(db.String(255), nullable=True)

    group: Mapped["TargetGroup"] = relationship("TargetGroup", back_populates="targets")
    tracking_link: Mapped["TrackingLink | None"] = relationship(
        "TrackingLink",
        back_populates="target",
        uselist=False,
        cascade="all, delete-orphan",
    )


class TrackingLink(db.Model):
    __tablename__ = "tracking_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        db.ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    token: Mapped[str] = mapped_column(
        db.String(64), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    target: Mapped["Target"] = relationship("Target", back_populates="tracking_link")
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction",
        back_populates="tracking_link",
        cascade="all, delete-orphan",
    )

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)


class Interaction(db.Model):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tracking_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        db.ForeignKey("tracking_links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(db.String(32), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(db.String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(db.String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tracking_link: Mapped["TrackingLink"] = relationship(
        "TrackingLink", back_populates="interactions"
    )
