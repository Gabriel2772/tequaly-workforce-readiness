from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Operation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operations"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="valid_period"),
        Index("ix_operations_period_status", "starts_at", "ends_at", "status"),
    )

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    client_name: Mapped[str] = mapped_column(String(180))
    base_location: Mapped[str] = mapped_column(String(80), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mobilization_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), index=True)
    budget_cents: Mapped[int | None] = mapped_column(Integer)


class OperationRoleDemand(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operation_role_demands"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        UniqueConstraint("operation_id", "role_id", "shift_code", name="role_shift"),
    )

    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id"), index=True
    )
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("roles.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    shift_code: Mapped[str] = mapped_column(String(32), default="default")
    priority: Mapped[int] = mapped_column(Integer, default=100)


class OperationRoleCompatibleRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operation_role_compatible_roles"
    __table_args__ = (UniqueConstraint("role_demand_id", "role_id", name="demand_compatible_role"),)

    role_demand_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operation_role_demands.id")
    )
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("roles.id"))
    preference_rank: Mapped[int] = mapped_column(Integer, default=100)


class OperationRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operation_requirements"

    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id"), index=True
    )
    role_demand_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operation_role_demands.id")
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(180))
    requirement_type: Mapped[str] = mapped_column(String(48))
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class RequirementQualificationMap(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "requirement_qualification_map"
    __table_args__ = (
        UniqueConstraint("requirement_id", "qualification_id", name="requirement_qualification"),
    )

    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operation_requirements.id")
    )
    qualification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("qualifications.id")
    )
    minimum_level: Mapped[str | None] = mapped_column(String(48))
    allows_training: Mapped[bool] = mapped_column(Boolean, default=False)


class EligibilityRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "eligibility_runs"

    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id"), index=True
    )
    rules_version: Mapped[str] = mapped_column(String(40))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    evaluated_count: Mapped[int] = mapped_column(Integer, default=0)
    eligible_count: Mapped[int] = mapped_column(Integer, default=0)
    trainable_count: Mapped[int] = mapped_column(Integer, default=0)
    ineligible_count: Mapped[int] = mapped_column(Integer, default=0)
    runtime_ms: Mapped[int | None] = mapped_column(Integer)


class EligibilityResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "eligibility_results"
    __table_args__ = (
        UniqueConstraint(
            "eligibility_run_id", "employee_id", "role_demand_id", name="run_candidate"
        ),
        Index("ix_eligibility_results_classification", "eligibility_run_id", "classification"),
    )

    eligibility_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("eligibility_runs.id")
    )
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    role_demand_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operation_role_demands.id")
    )
    classification: Mapped[str] = mapped_column(String(24))
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    gaps: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    required_training_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    incremental_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
