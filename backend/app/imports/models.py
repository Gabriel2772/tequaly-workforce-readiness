from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"
    __table_args__ = (Index("ix_import_batches_contract_hash", "contract_name", "source_hash"),)

    contract_name: Mapped[str] = mapped_column(String(80))
    contract_version: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255))
    source_hash: Mapped[str] = mapped_column(String(64))
    mapping: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    normalized_rows: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    validation_errors: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    total_rows: Mapped[int] = mapped_column(Integer)
    valid_rows: Mapped[int] = mapped_column(Integer)
    invalid_rows: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="previewed")
    actor_id: Mapped[str] = mapped_column(String(120))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
