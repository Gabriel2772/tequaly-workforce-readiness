from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, date, datetime, time
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.eligibility.types import (
    AssignmentWindow,
    AuthorizationFact,
    AvailabilityWindow,
    DemandEligibilityContext,
    EmployeeEligibilityContext,
    OperationalRestrictionFact,
    OperationEligibilityContext,
    QualificationFact,
    TrainingOption,
)
from app.operations.models import (
    Operation,
    OperationRequirement,
    OperationRoleCompatibleRole,
    OperationRoleDemand,
    RequirementQualificationMap,
)
from app.workforce.models import (
    Employee,
    EmployeeAssignment,
    EmployeeAuthorization,
    EmployeeAvailability,
    EmployeeOperationalRestriction,
    EmployeeQualification,
    OperationalRestriction,
    TrainingCatalog,
    TrainingSession,
)


class EligibilityOperationNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class PreparedDemand:
    demand_id: UUID
    requested_headcount: int
    context: DemandEligibilityContext
    employees: tuple[EmployeeEligibilityContext, ...]


@dataclass(frozen=True)
class PreparedCandidatePool:
    operation_id: UUID
    operation: OperationEligibilityContext
    demands: tuple[PreparedDemand, ...]
    input_hash: str
    candidate_count: int
    total_active_employees: int

    @property
    def evaluated_count(self) -> int:
        return sum(len(demand.employees) for demand in self.demands)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _expiry_at_end_of_day(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.max, tzinfo=UTC)


def _months_of_experience(hired_on: date | None, reference: datetime) -> int:
    if hired_on is None:
        return 0
    reference_date = reference.date()
    months = (reference_date.year - hired_on.year) * 12 + reference_date.month - hired_on.month
    if reference_date.day < hired_on.day:
        months -= 1
    return max(months, 0)


def _payload_uuid_set(payload: dict[str, object], key: str) -> frozenset[UUID]:
    raw = payload.get(key, ())
    values = [raw] if isinstance(raw, str) else raw
    if not isinstance(values, (list, tuple, set, frozenset)):
        return frozenset()
    parsed: set[UUID] = set()
    for value in values:
        try:
            parsed.add(UUID(str(value)))
        except (TypeError, ValueError):
            continue
    return frozenset(parsed)


def _payload_nonnegative_int(payload: dict[str, object], key: str) -> int:
    raw = payload.get(key, 0)
    if isinstance(raw, bool):
        return 0
    if isinstance(raw, int):
        return max(raw, 0)
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return 0


def _canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=str)
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def _snapshot_hash(
    operation: OperationEligibilityContext,
    demands: tuple[PreparedDemand, ...],
) -> str:
    payload = _canonical(
        {
            "operation": operation,
            "demands": demands,
        }
    )
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CandidatePoolBuilder:
    def __init__(self, session: Session) -> None:
        self._session = session

    def build(self, operation_id: UUID) -> PreparedCandidatePool:
        operation_record = self._session.get(Operation, operation_id)
        if operation_record is None:
            raise EligibilityOperationNotFoundError(str(operation_id))

        operation = OperationEligibilityContext(
            starts_at=_as_utc(operation_record.starts_at),
            ends_at=_as_utc(operation_record.ends_at),
            mobilization_deadline=(
                _as_utc(operation_record.mobilization_deadline)
                if operation_record.mobilization_deadline is not None
                else None
            ),
        )
        demand_records = tuple(
            self._session.scalars(
                select(OperationRoleDemand)
                .where(OperationRoleDemand.operation_id == operation_id)
                .order_by(OperationRoleDemand.priority, OperationRoleDemand.id)
            )
        )
        compatibility_rows = self._session.execute(
            select(
                OperationRoleCompatibleRole.role_demand_id,
                OperationRoleCompatibleRole.role_id,
            ).where(
                OperationRoleCompatibleRole.role_demand_id.in_(
                    [demand.id for demand in demand_records]
                )
            )
        ).all()
        compatible_roles: dict[UUID, set[UUID]] = {
            demand.id: {demand.role_id} for demand in demand_records
        }
        for demand_id, role_id in compatibility_rows:
            compatible_roles[demand_id].add(role_id)

        requirement_records = tuple(
            self._session.scalars(
                select(OperationRequirement).where(
                    OperationRequirement.operation_id == operation_id,
                    OperationRequirement.mandatory.is_(True),
                )
            )
        )
        qualification_maps = tuple(
            self._session.scalars(
                select(RequirementQualificationMap)
                .join(
                    OperationRequirement,
                    OperationRequirement.id == RequirementQualificationMap.requirement_id,
                )
                .where(
                    OperationRequirement.operation_id == operation_id,
                    OperationRequirement.mandatory.is_(True),
                )
            )
        )
        maps_by_requirement: dict[UUID, list[RequirementQualificationMap]] = {}
        for mapping in qualification_maps:
            maps_by_requirement.setdefault(mapping.requirement_id, []).append(mapping)

        contexts: dict[UUID, DemandEligibilityContext] = {}
        same_base_required: dict[UUID, bool] = {}
        for demand in demand_records:
            requirements = tuple(
                requirement
                for requirement in requirement_records
                if requirement.role_demand_id in {None, demand.id}
            )
            mappings = tuple(
                mapping
                for requirement in requirements
                for mapping in maps_by_requirement.get(requirement.id, ())
            )
            authorization_ids = frozenset(
                authorization_id
                for requirement in requirements
                for authorization_id in _payload_uuid_set(requirement.payload, "authorization_ids")
            )
            restriction_ids = frozenset(
                restriction_id
                for requirement in requirements
                for restriction_id in _payload_uuid_set(
                    requirement.payload, "applicable_restriction_ids"
                )
            )
            minimum_experience = max(
                (
                    _payload_nonnegative_int(requirement.payload, "minimum_experience_months")
                    for requirement in requirements
                ),
                default=0,
            )
            contexts[demand.id] = DemandEligibilityContext(
                demand_id=demand.id,
                compatible_role_ids=frozenset(compatible_roles[demand.id]),
                required_qualification_ids=frozenset(
                    mapping.qualification_id for mapping in mappings
                ),
                trainable_qualification_ids=frozenset(
                    mapping.qualification_id for mapping in mappings if mapping.allows_training
                ),
                required_authorization_ids=authorization_ids,
                applicable_restriction_ids=restriction_ids,
                minimum_experience_months=minimum_experience,
            )
            same_base_required[demand.id] = any(
                bool(requirement.payload.get("same_base_required", False))
                for requirement in requirements
            )

        all_role_ids = {
            role_id for context in contexts.values() for role_id in context.compatible_role_ids
        }
        employee_records = tuple(
            self._session.scalars(
                select(Employee)
                .where(
                    Employee.active.is_(True),
                    Employee.canonical_role_id.in_(all_role_ids),
                )
                .order_by(Employee.id)
            )
        )
        employee_ids = [employee.id for employee in employee_records]
        facts = self._load_employee_facts(employee_ids, operation_id, operation, contexts)

        employee_contexts: dict[UUID, EmployeeEligibilityContext] = {}
        for employee in employee_records:
            employee_contexts[employee.id] = EmployeeEligibilityContext(
                employee_id=employee.id,
                active=employee.active,
                role_id=employee.canonical_role_id,
                qualifications=tuple(
                    sorted(
                        facts["qualifications"].get(employee.id, ()),
                        key=lambda fact: (
                            str(fact.qualification_id),
                            fact.expires_on.isoformat() if fact.expires_on else "9999-12-31",
                        ),
                    )
                ),
                availability=tuple(
                    sorted(
                        facts["availability"].get(employee.id, ()),
                        key=lambda window: (window.starts_at, window.ends_at),
                    )
                ),
                assignments=tuple(
                    sorted(
                        facts["assignments"].get(employee.id, ()),
                        key=lambda assignment: (
                            assignment.starts_at,
                            str(assignment.assignment_id),
                        ),
                    )
                ),
                authorizations=tuple(
                    sorted(
                        facts["authorizations"].get(employee.id, ()),
                        key=lambda fact: (
                            str(fact.authorization_id),
                            fact.expires_on.isoformat() if fact.expires_on else "9999-12-31",
                        ),
                    )
                ),
                training_options=tuple(facts["training_options"]),
                restrictions=tuple(
                    sorted(
                        facts["restrictions"].get(employee.id, ()),
                        key=lambda fact: str(fact.restriction_id),
                    )
                ),
                experience_months=_months_of_experience(employee.hired_on, operation.starts_at),
            )

        prepared_demands = tuple(
            PreparedDemand(
                demand_id=demand.id,
                requested_headcount=demand.quantity,
                context=contexts[demand.id],
                employees=tuple(
                    employee_contexts[employee.id]
                    for employee in employee_records
                    if employee.canonical_role_id in contexts[demand.id].compatible_role_ids
                    and (
                        not same_base_required[demand.id]
                        or employee.base_location == operation_record.base_location
                    )
                ),
            )
            for demand in demand_records
        )
        unique_candidates = {
            employee.employee_id for demand in prepared_demands for employee in demand.employees
        }
        total_active = (
            self._session.scalar(
                select(func.count()).select_from(Employee).where(Employee.active.is_(True))
            )
            or 0
        )
        return PreparedCandidatePool(
            operation_id=operation_id,
            operation=operation,
            demands=prepared_demands,
            input_hash=_snapshot_hash(operation, prepared_demands),
            candidate_count=len(unique_candidates),
            total_active_employees=total_active,
        )

    def _load_employee_facts(
        self,
        employee_ids: list[UUID],
        operation_id: UUID,
        operation: OperationEligibilityContext,
        contexts: dict[UUID, DemandEligibilityContext],
    ) -> dict[str, Any]:
        grouped: dict[str, Any] = {
            "qualifications": {},
            "availability": {},
            "assignments": {},
            "authorizations": {},
            "restrictions": {},
            "training_options": [],
        }
        if not employee_ids:
            return grouped

        for qualification_row in self._session.scalars(
            select(EmployeeQualification).where(EmployeeQualification.employee_id.in_(employee_ids))
        ):
            grouped["qualifications"].setdefault(qualification_row.employee_id, []).append(
                QualificationFact(
                    qualification_row.qualification_id,
                    _expiry_at_end_of_day(qualification_row.expires_on),
                )
            )
        for availability_row in self._session.scalars(
            select(EmployeeAvailability).where(
                EmployeeAvailability.employee_id.in_(employee_ids),
                EmployeeAvailability.starts_at <= operation.ends_at,
                EmployeeAvailability.ends_at >= operation.starts_at,
            )
        ):
            grouped["availability"].setdefault(availability_row.employee_id, []).append(
                AvailabilityWindow(
                    _as_utc(availability_row.starts_at),
                    _as_utc(availability_row.ends_at),
                    availability_row.status,
                )
            )
        for assignment_row in self._session.scalars(
            select(EmployeeAssignment).where(
                EmployeeAssignment.employee_id.in_(employee_ids),
                EmployeeAssignment.operation_id != operation_id,
                EmployeeAssignment.starts_at < operation.ends_at,
                EmployeeAssignment.ends_at > operation.starts_at,
            )
        ):
            grouped["assignments"].setdefault(assignment_row.employee_id, []).append(
                AssignmentWindow(
                    assignment_row.id,
                    _as_utc(assignment_row.starts_at),
                    _as_utc(assignment_row.ends_at),
                    assignment_row.status,
                )
            )
        for authorization_row in self._session.scalars(
            select(EmployeeAuthorization).where(EmployeeAuthorization.employee_id.in_(employee_ids))
        ):
            grouped["authorizations"].setdefault(authorization_row.employee_id, []).append(
                AuthorizationFact(
                    authorization_row.authorization_id,
                    _expiry_at_end_of_day(authorization_row.expires_on),
                    authorization_row.scope_value,
                )
            )
        for link, restriction in self._session.execute(
            select(EmployeeOperationalRestriction, OperationalRestriction)
            .join(
                OperationalRestriction,
                OperationalRestriction.id == EmployeeOperationalRestriction.restriction_id,
            )
            .where(EmployeeOperationalRestriction.employee_id.in_(employee_ids))
        ).all():
            grouped["restrictions"].setdefault(link.employee_id, []).append(
                OperationalRestrictionFact(
                    restriction_id=restriction.id,
                    starts_at=_as_utc(link.starts_at) if link.starts_at else None,
                    ends_at=_as_utc(link.ends_at) if link.ends_at else None,
                    hard_constraint=restriction.hard_constraint,
                    scope_value=link.scope_value,
                )
            )

        required_qualifications = {
            qualification_id
            for context in contexts.values()
            for qualification_id in context.required_qualification_ids
        }
        if required_qualifications:
            for session_record, catalog in self._session.execute(
                select(TrainingSession, TrainingCatalog)
                .join(
                    TrainingCatalog,
                    TrainingCatalog.id == TrainingSession.training_catalog_id,
                )
                .where(
                    TrainingCatalog.active.is_(True),
                    TrainingCatalog.qualification_id.in_(required_qualifications),
                    TrainingSession.status.in_(("scheduled", "open")),
                )
                .order_by(TrainingSession.ends_at, TrainingCatalog.id)
            ).all():
                grouped["training_options"].append(
                    TrainingOption(
                        qualification_id=catalog.qualification_id,
                        training_catalog_id=catalog.id,
                        completes_at=_as_utc(session_record.ends_at),
                    )
                )
        return grouped


def find_candidate_pool(
    session: Session,
    operation_id: UUID,
) -> dict[UUID, list[EmployeeEligibilityContext]]:
    pool = CandidatePoolBuilder(session).build(operation_id)
    return {demand.demand_id: list(demand.employees) for demand in pool.demands}
