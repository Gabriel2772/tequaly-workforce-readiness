from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserMcpConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_mcp_connections"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "client_type",
            "name",
            name="uq_user_mcp_connection_name",
        ),
        Index("ix_user_mcp_connections_owner", "user_id", "updated_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("app_users.id"),
    )
    name: Mapped[str] = mapped_column(String(120))
    client_type: Mapped[str] = mapped_column(String(20))
    endpoint_url: Mapped[str] = mapped_column(String(2048))
    transport: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(String(1000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
