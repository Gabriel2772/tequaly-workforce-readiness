from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from typing import cast
from uuid import UUID, uuid5

from sqlalchemy import Table, func
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import FromClause

from app.auth.models import AppUser
from app.auth.security import hash_password
from app.decisions.models import CalibrationParameter, DecisionOutcome, DecisionRun
from app.demo.generator import DemoDataset
from app.operations.models import (
    Operation,
    OperationRequirement,
    OperationRoleDemand,
    RequirementQualificationMap,
)
from app.workforce.models import (
    Authorization,
    Employee,
    EmployeeAssignment,
    EmployeeAvailability,
    EmployeeCostProfile,
    EmployeeQualification,
    Qualification,
    Role,
    RoleAlias,
    RoleFamily,
    TrainingCatalog,
    TrainingSession,
)

DEMO_NAMESPACE = UUID("3ae5066a-d047-5db3-bbe8-902f6b75f257")
Row = dict[str, object]


@dataclass(frozen=True)
class SeedSummary:
    users: int
    role_families: int
    roles: int
    role_aliases: int
    qualifications: int
    authorizations: int
    training_catalog: int
    employees: int
    employee_qualifications: int
    employee_costs: int
    employee_availability: int
    employee_assignments: int
    operations: int
    role_demands: int
    training_sessions: int
    requirements: int
    decision_outcomes: int
    calibration_parameters: int


def stable_demo_id(seed: int, entity: str, natural_key: str) -> UUID:
    seed_namespace = uuid5(DEMO_NAMESPACE, str(seed))
    return uuid5(seed_namespace, f"{entity}:{natural_key}")


def _upsert_rows(session: Session, table_like: FromClause, rows: list[Row]) -> None:
    if not rows:
        return

    table = cast(Table, table_like)
    update_columns = [
        column
        for column in table.columns
        if column.name not in {"id", "created_at", "updated_at"} and column.name in rows[0]
    ]
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "sqlite":
        sqlite_statement = sqlite_insert(table)
        update_values = {
            column.name: getattr(sqlite_statement.excluded, column.name)
            for column in update_columns
        }
        if "updated_at" in table.c:
            update_values["updated_at"] = func.now()
        session.execute(
            sqlite_statement.on_conflict_do_update(
                index_elements=[table.c.id],
                set_=update_values,
            ),
            rows,
        )
        return

    if dialect_name == "postgresql":
        postgresql_statement = postgresql_insert(table)
        update_values = {
            column.name: getattr(postgresql_statement.excluded, column.name)
            for column in update_columns
        }
        if "updated_at" in table.c:
            update_values["updated_at"] = func.now()
        session.execute(
            postgresql_statement.on_conflict_do_update(
                index_elements=[table.c.id],
                set_=update_values,
            ),
            rows,
        )
        return

    raise RuntimeError(f"Unsupported seed dialect: {dialect_name}")


def seed_demo(session: Session, dataset: DemoDataset) -> SeedSummary:
    demo_id = partial(stable_demo_id, dataset.seed)
    demo_accounts = (
        ("viewer.demo", "Leitor de demonstração", "viewer"),
        ("planner.demo", "Planejador de demonstração", "planner"),
        ("admin.demo", "Administrador de demonstração", "admin"),
    )
    _upsert_rows(
        session,
        AppUser.__table__,
        [
            {
                "id": demo_id("app_user", username),
                "username": username,
                "email": f"{username}@tequaly.local",
                "display_name": display_name,
                "password_hash": hash_password(
                    "TequalyDemo!2026",
                    salt=hashlib.sha256(f"{dataset.seed}:{username}".encode()).digest()[:16],
                ),
                "role": role,
                "active": True,
                "last_login_at": None,
            }
            for username, display_name, role in demo_accounts
        ],
    )
    family_ids = {
        family.code: demo_id("role_family", family.code) for family in dataset.role_families
    }
    role_ids = {role.code: demo_id("role", role.code) for role in dataset.canonical_roles}
    qualification_ids = {
        qualification.code: demo_id("qualification", qualification.code)
        for qualification in dataset.qualifications
    }
    training_ids = {
        training.code: demo_id("training", training.code) for training in dataset.training_catalog
    }
    employee_ids = {
        employee.employee_number: demo_id("employee", employee.employee_number)
        for employee in dataset.employees
    }
    operation_ids = {
        operation.code: demo_id("operation", operation.code) for operation in dataset.operations
    }
    demand_ids = {
        (demand.operation_code, demand.role_code, demand.shift_code): demo_id(
            "role_demand",
            f"{demand.operation_code}:{demand.role_code}:{demand.shift_code}",
        )
        for demand in dataset.role_demands
    }

    _upsert_rows(
        session,
        RoleFamily.__table__,
        [
            {
                "id": family_ids[family.code],
                "code": family.code,
                "name": family.name,
                "active": True,
            }
            for family in dataset.role_families
        ],
    )
    _upsert_rows(
        session,
        Role.__table__,
        [
            {
                "id": role_ids[role.code],
                "family_id": family_ids[role.family_code],
                "code": role.code,
                "name": role.name,
                "active": True,
            }
            for role in dataset.canonical_roles
        ],
    )
    _upsert_rows(
        session,
        RoleAlias.__table__,
        [
            {
                "id": demo_id("role_alias", alias.normalized_title),
                "role_id": role_ids[alias.role_code],
                "source_title": alias.source_title,
                "normalized_title": alias.normalized_title,
            }
            for alias in dataset.role_aliases
        ],
    )
    _upsert_rows(
        session,
        Qualification.__table__,
        [
            {
                "id": qualification_ids[qualification.code],
                "code": qualification.code,
                "name": qualification.name,
                "category": qualification.category,
                "method": None,
                "level": None,
                "validity_days": qualification.validity_days,
                "active": True,
            }
            for qualification in dataset.qualifications
        ],
    )
    _upsert_rows(
        session,
        Authorization.__table__,
        [
            {
                "id": demo_id("authorization", authorization.code),
                "code": authorization.code,
                "name": authorization.name,
                "scope_type": authorization.scope_type,
                "active": True,
            }
            for authorization in dataset.authorizations
        ],
    )
    _upsert_rows(
        session,
        TrainingCatalog.__table__,
        [
            {
                "id": training_ids[training.code],
                "code": training.code,
                "name": training.name,
                "qualification_id": qualification_ids[training.qualification_code],
                "duration_minutes": training.duration_minutes,
                "cost_cents": training.cost_cents,
                "active": True,
            }
            for training in dataset.training_catalog
        ],
    )
    _upsert_rows(
        session,
        Operation.__table__,
        [
            {
                "id": operation_ids[operation.code],
                "code": operation.code,
                "name": operation.name,
                "client_name": operation.client_name,
                "base_location": operation.base_location,
                "starts_at": operation.starts_at,
                "ends_at": operation.ends_at,
                "mobilization_deadline": operation.mobilization_deadline,
                "status": operation.status,
                "budget_cents": operation.budget_cents,
            }
            for operation in dataset.operations
        ],
    )
    _upsert_rows(
        session,
        TrainingSession.__table__,
        [
            {
                "id": demo_id("training_session", training_session.code),
                "training_catalog_id": training_ids[training_session.training_code],
                "starts_at": training_session.starts_at,
                "ends_at": training_session.ends_at,
                "capacity": training_session.capacity,
                "base_location": training_session.base_location,
                "status": training_session.status,
            }
            for training_session in dataset.training_sessions
        ],
    )
    _upsert_rows(
        session,
        Employee.__table__,
        [
            {
                "id": employee_ids[employee.employee_number],
                "employee_number": employee.employee_number,
                "name": employee.name,
                "email": f"{employee.employee_number.casefold()}@example.invalid",
                "canonical_role_id": role_ids[employee.role_code],
                "base_location": employee.base_location,
                "seniority_level": employee.seniority_level,
                "hired_on": employee.hired_on,
                "active": employee.active,
            }
            for employee in dataset.employees
        ],
    )
    _upsert_rows(
        session,
        EmployeeCostProfile.__table__,
        [
            {
                "id": demo_id("employee_cost", cost.employee_number),
                "employee_id": employee_ids[cost.employee_number],
                "currency": "BRL",
                "hourly_cost_cents": cost.hourly_cost_cents,
                "travel_cost_cents": cost.travel_cost_cents,
                "effective_from": cost.effective_from,
                "effective_to": None,
            }
            for cost in dataset.employee_costs
        ],
    )
    _upsert_rows(
        session,
        EmployeeAvailability.__table__,
        [
            {
                "id": demo_id(
                    "employee_availability",
                    f"{window.employee_number}:{window.starts_at.isoformat()}",
                ),
                "employee_id": employee_ids[window.employee_number],
                "starts_at": window.starts_at,
                "ends_at": window.ends_at,
                "status": window.status,
            }
            for window in dataset.employee_availability
        ],
    )
    _upsert_rows(
        session,
        EmployeeAssignment.__table__,
        [
            {
                "id": demo_id(
                    "employee_assignment",
                    f"{assignment.employee_number}:{assignment.operation_code}",
                ),
                "employee_id": employee_ids[assignment.employee_number],
                "operation_id": operation_ids[assignment.operation_code],
                "starts_at": assignment.starts_at,
                "ends_at": assignment.ends_at,
                "status": assignment.status,
            }
            for assignment in dataset.employee_assignments
        ],
    )
    _upsert_rows(
        session,
        EmployeeQualification.__table__,
        [
            {
                "id": demo_id(
                    "employee_qualification",
                    f"{link.employee_number}:{link.qualification_code}",
                ),
                "employee_id": employee_ids[link.employee_number],
                "qualification_id": qualification_ids[link.qualification_code],
                "issued_on": link.issued_on,
                "expires_on": link.expires_on,
                "workload_minutes": None,
                "provider": "Provedor Sintético",
                "external_identifier": (
                    "DEMO-"
                    + demo_id(
                        "certificate",
                        f"{link.employee_number}:{link.qualification_code}",
                    ).hex[:12]
                ),
                "notes": "Registro gerado exclusivamente para demonstração.",
            }
            for link in dataset.employee_qualifications
        ],
    )
    _upsert_rows(
        session,
        OperationRoleDemand.__table__,
        [
            {
                "id": demand_ids[(demand.operation_code, demand.role_code, demand.shift_code)],
                "operation_id": operation_ids[demand.operation_code],
                "role_id": role_ids[demand.role_code],
                "quantity": demand.quantity,
                "shift_code": demand.shift_code,
                "priority": demand.priority,
            }
            for demand in dataset.role_demands
        ],
    )

    requirement_ids = {
        requirement.code: demo_id("operation_requirement", requirement.code)
        for requirement in dataset.requirements
    }
    _upsert_rows(
        session,
        OperationRequirement.__table__,
        [
            {
                "id": requirement_ids[requirement.code],
                "operation_id": operation_ids[requirement.operation_code],
                "role_demand_id": demand_ids[
                    (
                        requirement.operation_code,
                        requirement.role_code,
                        requirement.shift_code,
                    )
                ],
                "code": requirement.code,
                "name": f"Qualificação obrigatória {requirement.qualification_code}",
                "requirement_type": "qualification",
                "mandatory": True,
                "payload": {"source": "synthetic_demo"},
            }
            for requirement in dataset.requirements
        ],
    )
    _upsert_rows(
        session,
        RequirementQualificationMap.__table__,
        [
            {
                "id": demo_id("requirement_qualification", requirement.code),
                "requirement_id": requirement_ids[requirement.code],
                "qualification_id": qualification_ids[requirement.qualification_code],
                "minimum_level": None,
                "allows_training": requirement.allows_training,
            }
            for requirement in dataset.requirements
        ],
    )

    # The demonstration includes a small, explicitly synthetic history so the
    # human-in-the-loop calibration flow can be exercised without pretending
    # these observations came from Tequaly. The outlier is intentional: it
    # demonstrates why the calibration estimate uses robust statistics.
    historical_training_costs = (30_000, 31_000, 32_000, 33_000, 100_000)
    historical_runs: list[Row] = []
    historical_outcomes: list[Row] = []
    for operation, actual_cost_cents in zip(
        dataset.operations[:5], historical_training_costs, strict=True
    ):
        decision_run_id = demo_id("historical_decision_run", operation.code)
        predicted_ready_at = operation.mobilization_deadline
        predicted_cost_cents = 30_000
        historical_runs.append(
            {
                "id": decision_run_id,
                "operation_id": operation_ids[operation.code],
                "objective": "MIN_COST",
                "solver_version": "demo-history-v1",
                "rules_version": "1.0.0",
                "input_snapshot_hash": demo_id("historical_decision_hash", operation.code).hex * 2,
                "status": "OPTIMAL",
                "runtime_ms": 0,
                "metrics": {
                    "total_incremental_cost_cents": predicted_cost_cents,
                    "team_ready_at_epoch_minutes": int(predicted_ready_at.timestamp() // 60),
                },
                "candidate_snapshot": [],
                "created_by": "demo-seed",
            }
        )
        historical_outcomes.append(
            {
                "id": demo_id("historical_decision_outcome", operation.code),
                "decision_run_id": decision_run_id,
                "selected": True,
                "outcome_metrics": {
                    "actual_cost_cents": actual_cost_cents,
                    "actual_ready_at": predicted_ready_at.isoformat(),
                    "comparison": {
                        "cost": {
                            "predicted_cents": predicted_cost_cents,
                            "actual_cents": actual_cost_cents,
                            "variance_cents": actual_cost_cents - predicted_cost_cents,
                            "variance_percent": round(
                                (actual_cost_cents - predicted_cost_cents)
                                / predicted_cost_cents
                                * 100,
                                2,
                            ),
                        },
                        "readiness": {
                            "predicted_at": predicted_ready_at.isoformat(),
                            "actual_at": predicted_ready_at.isoformat(),
                            "variance_minutes": 0,
                            "status": "on_time",
                        },
                        "assignments": {"substitution_count": 0},
                        "training": {
                            "planned_count": 1,
                            "performed_count": 1,
                            "unperformed_count": 0,
                            "completion_percent": 100.0,
                        },
                    },
                    "substitutions": [],
                    "performed_training_action_ids": [],
                    "calibration_observations": [
                        {
                            "parameter": "training_cost_cents",
                            "category": "seguranca",
                            "value": str(actual_cost_cents),
                        }
                    ],
                },
                "recorded_by": "demo-seed",
            }
        )

    _upsert_rows(session, DecisionRun.__table__, historical_runs)
    _upsert_rows(session, DecisionOutcome.__table__, historical_outcomes)
    _upsert_rows(
        session,
        CalibrationParameter.__table__,
        [
            {
                "id": demo_id("calibration_parameter", "training_cost_cents:seguranca:v1"),
                "name": "training_cost_cents:seguranca",
                "version": "v1",
                "value": Decimal("30000"),
                "rationale": (
                    "Linha de base sintética para demonstração; não representa "
                    "um valor validado pela Tequaly."
                ),
            }
        ],
    )

    return SeedSummary(
        users=len(demo_accounts),
        role_families=len(dataset.role_families),
        roles=len(dataset.canonical_roles),
        role_aliases=len(dataset.role_aliases),
        qualifications=len(dataset.qualifications),
        authorizations=len(dataset.authorizations),
        training_catalog=len(dataset.training_catalog),
        employees=len(dataset.employees),
        employee_qualifications=len(dataset.employee_qualifications),
        employee_costs=len(dataset.employee_costs),
        employee_availability=len(dataset.employee_availability),
        employee_assignments=len(dataset.employee_assignments),
        operations=len(dataset.operations),
        role_demands=len(dataset.role_demands),
        training_sessions=len(dataset.training_sessions),
        requirements=len(dataset.requirements),
        decision_outcomes=len(historical_outcomes),
        calibration_parameters=1,
    )
