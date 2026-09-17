from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decisions.models import AuditEvent
from app.operations.models import (
    Operation,
    OperationRequirement,
    OperationRoleCompatibleRole,
    OperationRoleDemand,
    RequirementQualificationMap,
)
from app.operations.schemas import (
    OperationCreate,
    OperationRequirementUpdate,
    OperationRoleDemandUpdate,
    OperationUpdate,
)
from app.workforce.models import Qualification, Role


class DuplicateOperationError(ValueError):
    pass


class UnknownOperationReferenceError(ValueError):
    pass


class OperationNotFoundError(LookupError):
    pass


class InvalidOperationPeriodError(ValueError):
    pass


class OperationChildNotFoundError(LookupError):
    pass


class OperationService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def create(self, command: OperationCreate) -> Operation:
        code = command.code.strip().upper()
        if self._session.scalar(select(Operation.id).where(Operation.code == code)) is not None:
            raise DuplicateOperationError(code)

        role_ids = {
            demand.role_id
            for demand in command.demands
        } | {
            compatible_id
            for demand in command.demands
            for compatible_id in demand.compatible_role_ids
        }
        self._require_ids(Role, role_ids)
        qualification_ids = {
            qualification_id
            for requirement in command.requirements
            for qualification_id in requirement.qualification_ids
        }
        self._require_ids(Qualification, qualification_ids)

        operation = Operation(
            code=code,
            name=command.name.strip(),
            client_name=command.client_name.strip(),
            base_location=command.base_location.strip(),
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            mobilization_deadline=command.mobilization_deadline,
            status=command.status.strip(),
            budget_cents=command.budget_cents,
        )
        self._session.add(operation)
        self._session.flush()

        demands_by_role: dict[UUID, OperationRoleDemand] = {}
        for demand_command in command.demands:
            demand = OperationRoleDemand(
                operation_id=operation.id,
                role_id=demand_command.role_id,
                quantity=demand_command.quantity,
                shift_code=demand_command.shift_code.strip(),
                priority=demand_command.priority,
            )
            self._session.add(demand)
            self._session.flush()
            demands_by_role[demand.role_id] = demand
            for rank, role_id in enumerate(demand_command.compatible_role_ids, start=1):
                self._session.add(
                    OperationRoleCompatibleRole(
                        role_demand_id=demand.id,
                        role_id=role_id,
                        preference_rank=rank,
                    )
                )

        for requirement_command in command.requirements:
            role_demand_id = None
            if requirement_command.role_id is not None:
                matched_demand = demands_by_role.get(requirement_command.role_id)
                if matched_demand is None:
                    raise UnknownOperationReferenceError(
                        f"requirement role has no demand:{requirement_command.role_id}"
                    )
                role_demand_id = matched_demand.id
            requirement = OperationRequirement(
                operation_id=operation.id,
                role_demand_id=role_demand_id,
                code=requirement_command.code.strip().upper(),
                name=requirement_command.name.strip(),
                requirement_type=requirement_command.requirement_type.strip(),
                mandatory=requirement_command.mandatory,
                payload=requirement_command.payload,
            )
            self._session.add(requirement)
            self._session.flush()
            for qualification_id in requirement_command.qualification_ids:
                self._session.add(
                    RequirementQualificationMap(
                        requirement_id=requirement.id,
                        qualification_id=qualification_id,
                        minimum_level=requirement_command.minimum_level,
                        allows_training=requirement_command.allows_training,
                    )
                )

        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="operation.created",
                aggregate_type="operation",
                aggregate_id=operation.id,
                payload={
                    "code": operation.code,
                    "demand_count": len(command.demands),
                    "requirement_count": len(command.requirements),
                },
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        return operation

    def update(self, operation_id: UUID, command: OperationUpdate) -> Operation:
        operation = self._session.get(Operation, operation_id)
        if operation is None:
            raise OperationNotFoundError(str(operation_id))
        updates = command.model_dump(exclude_unset=True)
        starts_at = updates.get("starts_at", operation.starts_at)
        ends_at = updates.get("ends_at", operation.ends_at)
        if ends_at <= starts_at:
            raise InvalidOperationPeriodError("ends_at must be later than starts_at")
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(operation, field, value)
        self._session.flush()
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="operation.updated",
                aggregate_type="operation",
                aggregate_id=operation.id,
                payload={"changed_fields": sorted(updates)},
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        return operation

    def update_demand(
        self,
        operation_id: UUID,
        demand_id: UUID,
        command: OperationRoleDemandUpdate,
    ) -> OperationRoleDemand:
        demand = self._session.get(OperationRoleDemand, demand_id)
        if demand is None or demand.operation_id != operation_id:
            raise OperationChildNotFoundError(str(demand_id))
        if command.role_id is not None:
            self._require_ids(Role, {command.role_id})
        updates = command.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(demand, field, value)
        self._session.flush()
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="operation_demand.updated",
                aggregate_type="operation",
                aggregate_id=operation_id,
                payload={"demand_id": str(demand_id), "changed_fields": sorted(updates)},
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        return demand

    def update_requirement(
        self,
        operation_id: UUID,
        requirement_id: UUID,
        command: OperationRequirementUpdate,
    ) -> OperationRequirement:
        requirement = self._session.get(OperationRequirement, requirement_id)
        if requirement is None or requirement.operation_id != operation_id:
            raise OperationChildNotFoundError(str(requirement_id))
        updates = command.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(requirement, field, value)
        self._session.flush()
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="operation_requirement.updated",
                aggregate_type="operation",
                aggregate_id=operation_id,
                payload={
                    "requirement_id": str(requirement_id),
                    "changed_fields": sorted(updates),
                },
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        return requirement

    def _require_ids(self, model: type[Role] | type[Qualification], ids: set[UUID]) -> None:
        if not ids:
            return
        found = set(self._session.scalars(select(model.id).where(model.id.in_(ids))))
        missing = ids - found
        if missing:
            raise UnknownOperationReferenceError(
                f"unknown {model.__name__.lower()} ids:{','.join(sorted(map(str, missing)))}"
            )
