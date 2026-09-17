from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RoleFamily(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_families"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (Index("ix_roles_active_family", "active", "family_id"),)

    family_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("role_families.id"))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class RoleAlias(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_aliases"

    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("roles.id"), index=True)
    source_title: Mapped[str] = mapped_column(String(200))
    normalized_title: Mapped[str] = mapped_column(String(200), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_active_role", "active", "canonical_role_id"),
        Index("ix_employees_base_active", "base_location", "active"),
    )

    employee_number: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    canonical_role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("roles.id"))
    base_location: Mapped[str] = mapped_column(String(80))
    seniority_level: Mapped[str] = mapped_column(String(40))
    hired_on: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeRoleHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_role_history"
    __table_args__ = (
        CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="valid_period"),
        Index("ix_employee_role_history_period", "employee_id", "starts_on", "ends_on"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("roles.id"))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)


class Qualification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qualifications"

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(64), index=True)
    method: Mapped[str | None] = mapped_column(String(80))
    level: Mapped[str | None] = mapped_column(String(48))
    validity_days: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeQualification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_qualifications"
    __table_args__ = (
        UniqueConstraint("employee_id", "qualification_id", "issued_on", name="employee_issue"),
        Index("ix_employee_qualifications_expiry", "qualification_id", "expires_on"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), index=True
    )
    qualification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("qualifications.id")
    )
    issued_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    workload_minutes: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str | None] = mapped_column(String(160))
    external_identifier: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class Authorization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "authorizations"

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    scope_type: Mapped[str] = mapped_column(String(48))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeAuthorization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_authorizations"
    __table_args__ = (Index("ix_employee_authorizations_expiry", "authorization_id", "expires_on"),)

    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), index=True
    )
    authorization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("authorizations.id")
    )
    scope_value: Mapped[str | None] = mapped_column(String(160))
    issued_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)


class EmployeeAvailability(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_availability"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="valid_period"),
        Index("ix_employee_availability_period", "employee_id", "starts_at", "ends_at"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))


class EmployeeAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_assignments"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="valid_period"),
        Index("ix_employee_assignments_period", "employee_id", "starts_at", "ends_at"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    operation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id"), index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))


class EmployeeCostProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_cost_profiles"
    __table_args__ = (
        CheckConstraint("hourly_cost_cents >= 0", name="nonnegative_hourly_cost"),
        Index("ix_employee_cost_profiles_effective", "employee_id", "effective_from"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    hourly_cost_cents: Mapped[int] = mapped_column(Integer)
    travel_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class TechnicalCompetency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "technical_competencies"

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    scale_max: Mapped[int] = mapped_column(Integer, default=5)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeCompetency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_competencies"
    __table_args__ = (
        UniqueConstraint("employee_id", "competency_id", name="employee_competency"),
        CheckConstraint("level >= 0", name="nonnegative_level"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("technical_competencies.id")
    )
    level: Mapped[int] = mapped_column(Integer)
    assessed_on: Mapped[date] = mapped_column(Date)


class OperationalRestriction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operational_restrictions"

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    hard_constraint: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeOperationalRestriction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_operational_restrictions"
    __table_args__ = (
        Index("ix_employee_restrictions_period", "employee_id", "starts_at", "ends_at"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    restriction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operational_restrictions.id")
    )
    scope_value: Mapped[str | None] = mapped_column(String(160))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class TrainingCatalog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "training_catalog"

    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    qualification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("qualifications.id")
    )
    duration_minutes: Mapped[int] = mapped_column(Integer)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TrainingSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "training_sessions"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="valid_period"),)

    training_catalog_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_catalog.id")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    base_location: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32))


class EmployeeTrainingPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employee_training_plans"
    __table_args__ = (
        UniqueConstraint("employee_id", "training_session_id", name="employee_session"),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    training_session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_sessions.id")
    )
    operation_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("operations.id")
    )
    status: Mapped[str] = mapped_column(String(32))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
