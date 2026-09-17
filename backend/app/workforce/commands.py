from datetime import UTC, date, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.decisions.models import AuditEvent
from app.operations.models import Operation
from app.workforce.models import (
    Authorization,
    Employee,
    EmployeeAssignment,
    EmployeeAuthorization,
    EmployeeAvailability,
    EmployeeCompetency,
    EmployeeCostProfile,
    EmployeeOperationalRestriction,
    EmployeeQualification,
    OperationalRestriction,
    Qualification,
    Role,
    TechnicalCompetency,
)
from app.workforce.schemas import (
    EmployeeAssignmentCreate,
    EmployeeAssignmentUpdate,
    EmployeeAuthorizationCreate,
    EmployeeAuthorizationUpdate,
    EmployeeAvailabilityCreate,
    EmployeeAvailabilityUpdate,
    EmployeeCompetencyCreate,
    EmployeeCompetencyUpdate,
    EmployeeCostCreate,
    EmployeeCostUpdate,
    EmployeeCreate,
    EmployeeQualificationCreate,
    EmployeeQualificationUpdate,
    EmployeeRestrictionCreate,
    EmployeeRestrictionUpdate,
    EmployeeUpdate,
)

ModelT = TypeVar("ModelT", bound=Base)


class DuplicateEmployeeError(ValueError):
    pass


class UnknownRoleError(ValueError):
    pass


class EmployeeNotFoundForUpdateError(LookupError):
    pass


class UnknownReferenceError(ValueError):
    pass


class InvalidPeriodError(ValueError):
    pass


class ProfileRecordNotFoundError(LookupError):
    pass


class EmployeeCommandService:
    def __init__(self, session: Session, actor_id: str = "local-system") -> None:
        self._session = session
        self._actor_id = actor_id

    def create_employee(self, command: EmployeeCreate) -> Employee:
        duplicate = self._session.scalar(
            select(Employee.id).where(Employee.employee_number == command.employee_number.strip())
        )
        if duplicate is not None:
            raise DuplicateEmployeeError(command.employee_number)
        self._require_role(command.canonical_role_id)

        employee = Employee(
            employee_number=command.employee_number.strip(),
            name=command.name.strip(),
            email=command.email,
            canonical_role_id=command.canonical_role_id,
            base_location=command.base_location.strip(),
            seniority_level=command.seniority_level.strip(),
            hired_on=command.hired_on,
            active=command.active,
        )
        self._session.add(employee)
        self._session.flush()
        self._audit(
            event_type="employee.created",
            aggregate_type="employee",
            aggregate_id=employee.id,
            payload={"employee_number": employee.employee_number},
        )
        return employee

    def update_employee(self, employee_id: UUID, command: EmployeeUpdate) -> Employee:
        employee = self._session.get(Employee, employee_id)
        if employee is None:
            raise EmployeeNotFoundForUpdateError(str(employee_id))
        if command.canonical_role_id is not None:
            self._require_role(command.canonical_role_id)

        updates = command.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(employee, field, value)
        self._session.flush()
        self._audit(
            event_type="employee.updated",
            aggregate_type="employee",
            aggregate_id=employee.id,
            payload={"changed_fields": sorted(updates)},
        )
        return employee

    def add_qualification(self, employee_id: UUID, command: EmployeeQualificationCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_reference(Qualification, command.qualification_id)
        self._require_expiry(command.issued_on, command.expires_on)
        record = EmployeeQualification(
            employee_id=employee_id,
            qualification_id=command.qualification_id,
            issued_on=command.issued_on,
            expires_on=command.expires_on,
            workload_minutes=command.workload_minutes,
            provider=command.provider,
            external_identifier=command.external_identifier,
            notes=command.notes,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_qualification.created", record.id, employee_id)
        return record.id

    def update_qualification(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeQualificationUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeQualification, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        qualification_id = updates.get("qualification_id", record.qualification_id)
        self._require_reference(Qualification, qualification_id)
        issued_on = updates.get("issued_on", record.issued_on)
        expires_on = updates.get("expires_on", record.expires_on)
        self._require_expiry(issued_on, expires_on)
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_qualification.updated", record.id, employee_id)
        return record.id

    def add_authorization(self, employee_id: UUID, command: EmployeeAuthorizationCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_reference(Authorization, command.authorization_id)
        self._require_expiry(command.issued_on, command.expires_on)
        record = EmployeeAuthorization(
            employee_id=employee_id,
            authorization_id=command.authorization_id,
            scope_value=command.scope_value,
            issued_on=command.issued_on,
            expires_on=command.expires_on,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_authorization.created", record.id, employee_id)
        return record.id

    def update_authorization(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeAuthorizationUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeAuthorization, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        authorization_id = updates.get("authorization_id", record.authorization_id)
        self._require_reference(Authorization, authorization_id)
        issued_on = updates.get("issued_on", record.issued_on)
        expires_on = updates.get("expires_on", record.expires_on)
        self._require_expiry(issued_on, expires_on)
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_authorization.updated", record.id, employee_id)
        return record.id

    def add_availability(self, employee_id: UUID, command: EmployeeAvailabilityCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_period(command.starts_at, command.ends_at)
        self._require_nonoverlapping_availability(
            employee_id,
            command.starts_at,
            command.ends_at,
        )
        record = EmployeeAvailability(
            employee_id=employee_id,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            status=command.status,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_availability.created", record.id, employee_id)
        return record.id

    def update_availability(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeAvailabilityUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeAvailability, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        starts_at = updates.get("starts_at", record.starts_at)
        ends_at = updates.get("ends_at", record.ends_at)
        self._require_period(starts_at, ends_at)
        self._require_nonoverlapping_availability(
            employee_id,
            starts_at,
            ends_at,
            exclude_id=record.id,
        )
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_availability.updated", record.id, employee_id)
        return record.id

    def add_assignment(self, employee_id: UUID, command: EmployeeAssignmentCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_reference(Operation, command.operation_id)
        self._require_period(command.starts_at, command.ends_at)
        record = EmployeeAssignment(
            employee_id=employee_id,
            operation_id=command.operation_id,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            status=command.status,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_assignment.created", record.id, employee_id)
        return record.id

    def update_assignment(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeAssignmentUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeAssignment, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        operation_id = updates.get("operation_id", record.operation_id)
        self._require_reference(Operation, operation_id)
        starts_at = updates.get("starts_at", record.starts_at)
        ends_at = updates.get("ends_at", record.ends_at)
        self._require_period(starts_at, ends_at)
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_assignment.updated", record.id, employee_id)
        return record.id

    def add_cost(self, employee_id: UUID, command: EmployeeCostCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_effective_period(command.effective_from, command.effective_to)
        record = EmployeeCostProfile(
            employee_id=employee_id,
            currency=command.currency.upper(),
            hourly_cost_cents=command.hourly_cost_cents,
            travel_cost_cents=command.travel_cost_cents,
            effective_from=command.effective_from,
            effective_to=command.effective_to,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_cost.created", record.id, employee_id)
        return record.id

    def update_cost(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeCostUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeCostProfile, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        effective_from = updates.get("effective_from", record.effective_from)
        effective_to = updates.get("effective_to", record.effective_to)
        self._require_effective_period(effective_from, effective_to)
        if "currency" in updates and updates["currency"] is not None:
            updates["currency"] = updates["currency"].upper()
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_cost.updated", record.id, employee_id)
        return record.id

    def add_competency(self, employee_id: UUID, command: EmployeeCompetencyCreate) -> UUID:
        self._require_employee(employee_id)
        competency = self._require_reference(TechnicalCompetency, command.competency_id)
        if command.level > competency.scale_max:
            raise UnknownReferenceError("Competency level exceeds its scale")
        record = EmployeeCompetency(
            employee_id=employee_id,
            competency_id=command.competency_id,
            level=command.level,
            assessed_on=command.assessed_on,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_competency.created", record.id, employee_id)
        return record.id

    def update_competency(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeCompetencyUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeCompetency, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        competency_id = updates.get("competency_id", record.competency_id)
        competency = self._require_reference(TechnicalCompetency, competency_id)
        level = updates.get("level", record.level)
        if level > competency.scale_max:
            raise UnknownReferenceError("Competency level exceeds its scale")
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_competency.updated", record.id, employee_id)
        return record.id

    def add_restriction(self, employee_id: UUID, command: EmployeeRestrictionCreate) -> UUID:
        self._require_employee(employee_id)
        self._require_reference(OperationalRestriction, command.restriction_id)
        if command.starts_at and command.ends_at:
            self._require_period(command.starts_at, command.ends_at)
        record = EmployeeOperationalRestriction(
            employee_id=employee_id,
            restriction_id=command.restriction_id,
            scope_value=command.scope_value,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            notes=command.notes,
        )
        self._session.add(record)
        self._session.flush()
        self._audit_profile_record("employee_restriction.created", record.id, employee_id)
        return record.id

    def update_restriction(
        self,
        employee_id: UUID,
        record_id: UUID,
        command: EmployeeRestrictionUpdate,
    ) -> UUID:
        record = self._owned_record(EmployeeOperationalRestriction, employee_id, record_id)
        updates = command.model_dump(exclude_unset=True)
        restriction_id = updates.get("restriction_id", record.restriction_id)
        self._require_reference(OperationalRestriction, restriction_id)
        starts_at = updates.get("starts_at", record.starts_at)
        ends_at = updates.get("ends_at", record.ends_at)
        if starts_at is not None and ends_at is not None:
            self._require_period(starts_at, ends_at)
        self._apply_updates(record, updates)
        self._session.flush()
        self._audit_profile_record("employee_restriction.updated", record.id, employee_id)
        return record.id

    def _require_role(self, role_id: UUID) -> None:
        if self._session.get(Role, role_id) is None:
            raise UnknownRoleError(str(role_id))

    def _require_employee(self, employee_id: UUID) -> None:
        if self._session.get(Employee, employee_id) is None:
            raise EmployeeNotFoundForUpdateError(str(employee_id))

    def _require_reference(self, model: type[ModelT], record_id: UUID) -> ModelT:
        record = self._session.get(model, record_id)
        if record is None:
            raise UnknownReferenceError(f"{model.__name__}:{record_id}")
        return record

    def _owned_record(
        self,
        model: type[ModelT],
        employee_id: UUID,
        record_id: UUID,
    ) -> ModelT:
        record = self._session.get(model, record_id)
        if record is None or getattr(record, "employee_id", None) != employee_id:
            raise ProfileRecordNotFoundError(f"{model.__name__}:{record_id}")
        return record

    @staticmethod
    def _apply_updates(record: Base, updates: dict[str, object]) -> None:
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(record, field, value)

    @staticmethod
    def _require_period(starts_at: datetime, ends_at: datetime) -> None:
        if ends_at <= starts_at:
            raise InvalidPeriodError("ends_at must be later than starts_at")

    @staticmethod
    def _require_expiry(issued_on: date, expires_on: date | None) -> None:
        if expires_on is not None and expires_on < issued_on:
            raise InvalidPeriodError("expires_on must be on or after issued_on")

    @staticmethod
    def _require_effective_period(effective_from: date, effective_to: date | None) -> None:
        if effective_to is not None and effective_to < effective_from:
            raise InvalidPeriodError("effective_to must be on or after effective_from")

    def _require_nonoverlapping_availability(
        self,
        employee_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_id: UUID | None = None,
    ) -> None:
        statement = select(EmployeeAvailability.id).where(
            EmployeeAvailability.employee_id == employee_id,
            EmployeeAvailability.starts_at < ends_at,
            EmployeeAvailability.ends_at > starts_at,
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeAvailability.id != exclude_id)
        overlap = self._session.scalar(statement)
        if overlap is not None:
            raise InvalidPeriodError("availability period overlaps an existing record")

    def _audit_profile_record(
        self,
        event_type: str,
        record_id: UUID,
        employee_id: UUID,
    ) -> None:
        self._audit(
            event_type=event_type,
            aggregate_type="employee",
            aggregate_id=employee_id,
            payload={"record_id": str(record_id)},
        )

    def _audit(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID,
        payload: dict[str, object],
    ) -> None:
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                payload=payload,
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
