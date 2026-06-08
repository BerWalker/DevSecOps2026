import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from services.analytics.extensions import db


class ClickEvent(db.Model):
    __tablename__ = "click_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(db.String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(db.String(32), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(db.String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(db.String(512), nullable=True)
    country: Mapped[str | None] = mapped_column(db.String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(db.String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(db.String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(db.Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(db.Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
