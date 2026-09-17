from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DecisionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_runs"
    __table_args__ = (Index("ix_decision_runs_operation_created", "operation_id", "created_at"),)

    operation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("operations.id"))
    objective: Mapped[str] = mapped_column(String(48))
    solver_version: Mapped[str] = mapped_column(String(40))
    rules_version: Mapped[str] = mapped_column(String(40))
    input_snapshot_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    candidate_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(120))


class DecisionAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_assignments"

    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id"), index=True
    )
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    role_demand_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operation_role_demands.id")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    incremental_cost_cents: Mapped[int] = mapped_column(Integer, default=0)


class DecisionTrainingAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_training_actions"

    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id"), index=True
    )
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    training_catalog_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_catalog.id")
    )
    training_session_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_sessions.id")
    )
    ready_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)


class DecisionSelection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "decision_selections"
    __table_args__ = (
        Index("ix_decision_selections_operation_active", "operation_id", "superseded_at"),
    )

    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id"), index=True
    )
    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(String(500))
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by_selection_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_selections.id")
    )


class DecisionOutcome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_outcomes"

    decision_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decision_runs.id"), unique=True
    )
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome_metrics: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    recorded_by: Mapped[str] = mapped_column(String(120))


class CalibrationParameter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calibration_parameters"
    __table_args__ = (
        Index("ix_calibration_parameters_name_version", "name", "version", unique=True),
    )

    name: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(40))
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    rationale: Mapped[str | None] = mapped_column(String(500))


class CalibrationSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calibration_suggestions"
    __table_args__ = (
        Index(
            "ix_calibration_suggestions_parameter_status",
            "parameter_name",
            "category",
            "status",
        ),
    )

    parameter_name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(160))
    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    proposed_value: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    sample_size: Mapped[int] = mapped_column(Integer)
    confidence_basis: Mapped[str] = mapped_column(String(80))
    interquartile_range: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    rationale: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_by: Mapped[str] = mapped_column(String(120))
    applied_by: Mapped[str | None] = mapped_column(String(120))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_parameter_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("calibration_parameters.id")
    )


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_aggregate", "aggregate_type", "aggregate_id", "occurred_at"),
    )

    actor_id: Mapped[str | None] = mapped_column(String(120))
    event_type: Mapped[str] = mapped_column(String(80))
    aggregate_type: Mapped[str] = mapped_column(String(80))
    aggregate_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
