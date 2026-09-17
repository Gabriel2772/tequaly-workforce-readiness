from datetime import UTC, date, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decisions.models import AuditEvent
from app.imports.models import ImportBatch
from app.imports.types import ImportCommitSummary, ImportContractName
from app.operations.models import (
    Operation,
    OperationRequirement,
    OperationRoleDemand,
    RequirementQualificationMap,
)
from app.workforce.models import (
    Employee,
    EmployeeQualification,
    Qualification,
    Role,
    TrainingCatalog,
)


class ImportCommitError(RuntimeError):
    pass


def _date(value: object) -> date:
    return date.fromisoformat(str(value))


def _datetime(value: object) -> datetime:
    return datetime.fromisoformat(str(value))


class ImportCommitService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def commit(self, token: UUID, *, confirmed: bool) -> ImportCommitSummary:
        batch = self._session.get(ImportBatch, token)
        if batch is None:
            raise ImportCommitError("preview_not_found")
        contract = cast(ImportContractName, batch.contract_name)
        if batch.status == "committed":
            return ImportCommitSummary(
                batch_id=batch.id,
                contract=contract,
                created=0,
                updated=0,
                total=batch.total_rows,
                idempotent=True,
            )
        if not confirmed:
            raise ImportCommitError("confirmation_required")
        now = datetime.now(UTC)
        expires_at = batch.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            raise ImportCommitError("preview_expired")
        if batch.invalid_rows or batch.validation_errors:
            raise ImportCommitError("preview_has_errors")

        created, updated = self._persist(contract, batch.normalized_rows)
        batch.status = "committed"
        batch.committed_at = now
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="import.committed",
                aggregate_type="import_batch",
                aggregate_id=batch.id,
                payload={
                    "contract": contract,
                    "contract_version": batch.contract_version,
                    "source_hash": batch.source_hash,
                    "created": created,
                    "updated": updated,
                },
                occurred_at=now,
            )
        )
        self._session.flush()
        return ImportCommitSummary(
            batch_id=batch.id,
            contract=contract,
            created=created,
            updated=updated,
            total=batch.total_rows,
        )

    def _persist(
        self, contract: ImportContractName, rows: list[dict[str, object]]
    ) -> tuple[int, int]:
        if contract == "employees":
            return self._employees(rows)
        if contract == "employee_qualifications":
            return self._employee_qualifications(rows)
        if contract == "operations":
            return self._operations(rows)
        return self._training_catalog(rows)

    def _employees(self, rows: list[dict[str, object]]) -> tuple[int, int]:
        roles = {role.code: role.id for role in self._session.scalars(select(Role))}
        existing = {
            employee.employee_number: employee
            for employee in self._session.scalars(
                select(Employee).where(
                    Employee.employee_number.in_([str(row["employee_number"]) for row in rows])
                )
            )
        }
        created = updated = 0
        for row in rows:
            number = str(row["employee_number"])
            employee = existing.get(number)
            if employee is None:
                employee = Employee(employee_number=number)
                self._session.add(employee)
                existing[number] = employee
                created += 1
            else:
                updated += 1
            employee.name = str(row["name"])
            employee.email = str(row["email"]) if row.get("email") else None
            employee.canonical_role_id = roles[str(row["role_code"])]
            employee.base_location = str(row["base_location"])
            employee.seniority_level = str(row["seniority_level"])
            employee.hired_on = _date(row["hired_on"])
            employee.active = bool(row["active"])
        return created, updated

    def _employee_qualifications(self, rows: list[dict[str, object]]) -> tuple[int, int]:
        employees = {
            employee.employee_number: employee.id
            for employee in self._session.scalars(select(Employee))
        }
        qualifications = {
            qualification.code: qualification.id
            for qualification in self._session.scalars(select(Qualification))
        }
        created = updated = 0
        for row in rows:
            employee_id = employees[str(row["employee_number"])]
            qualification_id = qualifications[str(row["qualification_code"])]
            issued_on = _date(row["issued_on"])
            record = self._session.scalar(
                select(EmployeeQualification).where(
                    EmployeeQualification.employee_id == employee_id,
                    EmployeeQualification.qualification_id == qualification_id,
                    EmployeeQualification.issued_on == issued_on,
                )
            )
            if record is None:
                record = EmployeeQualification(
                    employee_id=employee_id,
                    qualification_id=qualification_id,
                    issued_on=issued_on,
                )
                self._session.add(record)
                created += 1
            else:
                updated += 1
            record.expires_on = _date(row["expires_on"]) if row.get("expires_on") else None
            record.provider = str(row["provider"]) if row.get("provider") else None
            record.external_identifier = (
                str(row["external_identifier"]) if row.get("external_identifier") else None
            )
        return created, updated

    def _operations(self, rows: list[dict[str, object]]) -> tuple[int, int]:
        roles = {role.code: role.id for role in self._session.scalars(select(Role))}
        qualifications = {
            qualification.code: qualification.id
            for qualification in self._session.scalars(select(Qualification))
        }
        existing_operations = {
            operation.code: operation
            for operation in self._session.scalars(
                select(Operation).where(Operation.code.in_({str(row["code"]) for row in rows}))
            )
        }
        created = updated = 0
        for row in rows:
            code = str(row["code"])
            operation = existing_operations.get(code)
            if operation is None:
                operation = Operation(code=code)
                self._session.add(operation)
                self._session.flush()
                existing_operations[code] = operation
                created += 1
            else:
                updated += 1
            operation.name = str(row["name"])
            operation.client_name = str(row["client_name"])
            operation.base_location = str(row["base_location"])
            operation.starts_at = _datetime(row["starts_at"])
            operation.ends_at = _datetime(row["ends_at"])
            operation.mobilization_deadline = _datetime(row["mobilization_deadline"])
            operation.status = str(row["status"])
            operation.budget_cents = int(str(row["budget_cents"]))
            role_id = roles[str(row["role_code"])]
            shift_code = str(row["shift_code"])
            demand = self._session.scalar(
                select(OperationRoleDemand).where(
                    OperationRoleDemand.operation_id == operation.id,
                    OperationRoleDemand.role_id == role_id,
                    OperationRoleDemand.shift_code == shift_code,
                )
            )
            if demand is None:
                demand = OperationRoleDemand(
                    operation_id=operation.id,
                    role_id=role_id,
                    shift_code=shift_code,
                )
                self._session.add(demand)
                self._session.flush()
            demand.quantity = int(str(row["quantity"]))
            demand.priority = int(str(row["priority"]))
            if row.get("qualification_code"):
                qualification_code = str(row["qualification_code"])
                requirement_code = f"IMP-{qualification_code}-{shift_code}"[:64]
                requirement = self._session.scalar(
                    select(OperationRequirement).where(
                        OperationRequirement.operation_id == operation.id,
                        OperationRequirement.role_demand_id == demand.id,
                        OperationRequirement.code == requirement_code,
                    )
                )
                if requirement is None:
                    requirement = OperationRequirement(
                        operation_id=operation.id,
                        role_demand_id=demand.id,
                        code=requirement_code,
                        name=f"Qualifica��o obrigat�ria {qualification_code}",
                        requirement_type="qualification",
                        mandatory=True,
                        payload={"source": "canonical_import"},
                    )
                    self._session.add(requirement)
                    self._session.flush()
                qualification_id = qualifications[qualification_code]
                mapping = self._session.scalar(
                    select(RequirementQualificationMap).where(
                        RequirementQualificationMap.requirement_id == requirement.id,
                        RequirementQualificationMap.qualification_id == qualification_id,
                    )
                )
                if mapping is None:
                    self._session.add(
                        RequirementQualificationMap(
                            requirement_id=requirement.id,
                            qualification_id=qualification_id,
                            minimum_level=None,
                            allows_training=bool(row["allows_training"]),
                        )
                    )
                else:
                    mapping.allows_training = bool(row["allows_training"])
        return created, updated

    def _training_catalog(self, rows: list[dict[str, object]]) -> tuple[int, int]:
        qualifications = {
            qualification.code: qualification.id
            for qualification in self._session.scalars(select(Qualification))
        }
        existing = {
            training.code: training
            for training in self._session.scalars(
                select(TrainingCatalog).where(
                    TrainingCatalog.code.in_([str(row["code"]) for row in rows])
                )
            )
        }
        created = updated = 0
        for row in rows:
            code = str(row["code"])
            training = existing.get(code)
            if training is None:
                training = TrainingCatalog(code=code)
                self._session.add(training)
                existing[code] = training
                created += 1
            else:
                updated += 1
            training.name = str(row["name"])
            training.qualification_id = qualifications[str(row["qualification_code"])]
            training.duration_minutes = int(str(row["duration_minutes"]))
            training.cost_cents = int(str(row["cost_cents"]))
            training.active = bool(row["active"])
        return created, updated
