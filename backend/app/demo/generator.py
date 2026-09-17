from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.demo.catalogs import (
    AUTHORIZATION_NAMES,
    BASES,
    QUALIFICATION_NAMES,
    ROLE_CATALOG,
)

REFERENCE_DATE = date(2026, 8, 10)


@dataclass(frozen=True)
class RoleFamilySeed:
    code: str
    name: str


@dataclass(frozen=True)
class RoleSeed:
    code: str
    name: str
    family_code: str


@dataclass(frozen=True)
class RoleAliasSeed:
    source_title: str
    normalized_title: str
    role_code: str


@dataclass(frozen=True)
class QualificationSeed:
    code: str
    name: str
    category: str
    validity_days: int | None


@dataclass(frozen=True)
class AuthorizationSeed:
    code: str
    name: str
    scope_type: str


@dataclass(frozen=True)
class TrainingSeed:
    code: str
    name: str
    qualification_code: str
    duration_minutes: int
    cost_cents: int


@dataclass(frozen=True)
class EmployeeSeed:
    employee_number: str
    name: str
    role_code: str
    base_location: str
    seniority_level: str
    hired_on: date
    active: bool


@dataclass(frozen=True)
class EmployeeQualificationSeed:
    employee_number: str
    qualification_code: str
    issued_on: date
    expires_on: date | None


@dataclass(frozen=True)
class EmployeeCostSeed:
    employee_number: str
    hourly_cost_cents: int
    travel_cost_cents: int
    effective_from: date


@dataclass(frozen=True)
class OperationSeed:
    code: str
    name: str
    client_name: str
    base_location: str
    starts_at: datetime
    ends_at: datetime
    mobilization_deadline: datetime
    status: str
    budget_cents: int


@dataclass(frozen=True)
class RoleDemandSeed:
    operation_code: str
    role_code: str
    quantity: int
    shift_code: str
    priority: int


@dataclass(frozen=True)
class EmployeeAssignmentSeed:
    employee_number: str
    operation_code: str
    starts_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True)
class EmployeeAvailabilitySeed:
    employee_number: str
    starts_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True)
class TrainingSessionSeed:
    code: str
    training_code: str
    starts_at: datetime
    ends_at: datetime
    capacity: int
    base_location: str
    status: str


@dataclass(frozen=True)
class RequirementSeed:
    code: str
    operation_code: str
    role_code: str
    shift_code: str
    qualification_code: str
    allows_training: bool


@dataclass(frozen=True)
class DemoDataset:
    seed: int
    bases: tuple[str, ...]
    role_families: tuple[RoleFamilySeed, ...]
    canonical_roles: tuple[RoleSeed, ...]
    role_aliases: tuple[RoleAliasSeed, ...]
    qualifications: tuple[QualificationSeed, ...]
    authorizations: tuple[AuthorizationSeed, ...]
    training_catalog: tuple[TrainingSeed, ...]
    employees: tuple[EmployeeSeed, ...]
    employee_qualifications: tuple[EmployeeQualificationSeed, ...]
    employee_costs: tuple[EmployeeCostSeed, ...]
    operations: tuple[OperationSeed, ...]
    role_demands: tuple[RoleDemandSeed, ...]
    employee_availability: tuple[EmployeeAvailabilitySeed, ...]
    employee_assignments: tuple[EmployeeAssignmentSeed, ...]
    training_sessions: tuple[TrainingSessionSeed, ...]
    requirements: tuple[RequirementSeed, ...]


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return "-".join(ascii_value.casefold().replace("/", " ").split())


def _build_roles() -> tuple[tuple[RoleFamilySeed, ...], tuple[RoleSeed, ...]]:
    families: list[RoleFamilySeed] = []
    roles: list[RoleSeed] = []
    for family_index, (family_name, role_names) in enumerate(ROLE_CATALOG.items(), start=1):
        family_code = f"FAM-{family_index:02d}"
        families.append(RoleFamilySeed(code=family_code, name=family_name))
        for role_index, role_name in enumerate(role_names, start=1):
            roles.append(
                RoleSeed(
                    code=f"{family_code}-R{role_index:02d}",
                    name=role_name,
                    family_code=family_code,
                )
            )
    return tuple(families), tuple(roles)


def _build_aliases(roles: tuple[RoleSeed, ...]) -> tuple[RoleAliasSeed, ...]:
    aliases = [
        RoleAliasSeed(
            source_title=role.name,
            normalized_title=_slug(role.name),
            role_code=role.code,
        )
        for role in roles
    ]
    aliases.extend(
        RoleAliasSeed(
            source_title=f"{role.name} Pleno",
            normalized_title=f"{_slug(role.name)}-pleno",
            role_code=role.code,
        )
        for role in roles[:40]
    )
    return tuple(aliases)


def _qualification_category(index: int) -> str:
    boundaries = (20, 32, 42, 52, 60, 66, 72)
    categories = (
        "seguran�a",
        "soldagem",
        "inspe��o",
        "equipamentos",
        "t�cnica",
        "gest�o",
        "digital",
    )
    return next(
        category
        for boundary, category in zip(boundaries, categories, strict=True)
        if index <= boundary
    )


def _build_qualifications() -> tuple[QualificationSeed, ...]:
    return tuple(
        QualificationSeed(
            code=f"QLF-{index:03d}",
            name=name,
            category=_qualification_category(index),
            validity_days=None if index % 9 == 0 else 730,
        )
        for index, name in enumerate(QUALIFICATION_NAMES, start=1)
    )


def _build_authorizations() -> tuple[AuthorizationSeed, ...]:
    return tuple(
        AuthorizationSeed(
            code=f"AUT-{index:03d}",
            name=name,
            scope_type=("cliente", "unidade", "equipamento")[index % 3],
        )
        for index, name in enumerate(AUTHORIZATION_NAMES, start=1)
    )


def _build_training_catalog(
    qualifications: tuple[QualificationSeed, ...],
) -> tuple[TrainingSeed, ...]:
    return tuple(
        TrainingSeed(
            code=f"TRN-{index:03d}",
            name=f"Forma��o: {qualification.name}",
            qualification_code=qualification.code,
            duration_minutes=(8 + index % 5 * 4) * 60,
            cost_cents=(90_000 + index * 7_500),
        )
        for index, qualification in enumerate(qualifications[:24], start=1)
    )


def _build_employees(
    rng: random.Random,
    roles: tuple[RoleSeed, ...],
    employee_count: int,
) -> tuple[EmployeeSeed, ...]:
    role_weights = [3 if role.family_code in {"FAM-07", "FAM-08"} else 1 for role in roles]
    employees: list[EmployeeSeed] = []
    for index in range(1, employee_count + 1):
        role = rng.choices(roles, weights=role_weights, k=1)[0]
        employees.append(
            EmployeeSeed(
                employee_number=f"SYN-{index:05d}",
                name=f"Colaborador Sint�tico {index:05d}",
                role_code=role.code,
                base_location=rng.choices(BASES, weights=(34, 23, 18, 15, 10), k=1)[0],
                seniority_level=rng.choices(
                    ("j�nior", "pleno", "s�nior", "especialista"),
                    weights=(28, 42, 24, 6),
                    k=1,
                )[0],
                hired_on=REFERENCE_DATE - timedelta(days=rng.randint(60, 7_300)),
                active=rng.random() >= 0.03,
            )
        )
    return tuple(employees)


def _build_employee_qualifications(
    rng: random.Random,
    employees: tuple[EmployeeSeed, ...],
    qualifications: tuple[QualificationSeed, ...],
) -> tuple[EmployeeQualificationSeed, ...]:
    links: list[EmployeeQualificationSeed] = []
    for index, employee in enumerate(employees, start=1):
        selected = rng.sample(qualifications, k=3 + index % 5)
        for qualification_index, qualification in enumerate(selected):
            issued_on = REFERENCE_DATE - timedelta(days=30 + rng.randint(0, 600))
            if qualification.validity_days is None:
                expires_on = None
            elif qualification_index == 0 and index % 17 == 0:
                expires_on = REFERENCE_DATE - timedelta(days=1 + index % 90)
            elif qualification_index == 0 and index % 19 == 0:
                expires_on = REFERENCE_DATE + timedelta(days=1 + index % 30)
            else:
                expires_on = issued_on + timedelta(days=qualification.validity_days)
            links.append(
                EmployeeQualificationSeed(
                    employee_number=employee.employee_number,
                    qualification_code=qualification.code,
                    issued_on=issued_on,
                    expires_on=expires_on,
                )
            )
    return tuple(links)


def _build_employee_costs(employees: tuple[EmployeeSeed, ...]) -> tuple[EmployeeCostSeed, ...]:
    seniority_costs = {
        "j�nior": 6_500,
        "pleno": 9_000,
        "s�nior": 12_500,
        "especialista": 16_000,
    }
    return tuple(
        EmployeeCostSeed(
            employee_number=employee.employee_number,
            hourly_cost_cents=seniority_costs[employee.seniority_level] + index % 17 * 125,
            travel_cost_cents=25_000 + BASES.index(employee.base_location) * 12_500,
            effective_from=REFERENCE_DATE,
        )
        for index, employee in enumerate(employees, start=1)
    )


def _build_operations(
    roles: tuple[RoleSeed, ...],
) -> tuple[tuple[OperationSeed, ...], tuple[RoleDemandSeed, ...]]:
    start = datetime(2026, 10, 1, 8, tzinfo=UTC)
    operations: list[OperationSeed] = []
    demands: list[RoleDemandSeed] = []
    for index in range(1, 9):
        operation_start = start + timedelta(days=(index - 1) * 21)
        operation_code = f"OPS-SYN-{index:02d}"
        operations.append(
            OperationSeed(
                code=operation_code,
                name=f"Opera��o Sint�tica {index:02d}",
                client_name=f"Cliente Demonstra��o {index:02d}",
                base_location=BASES[(index - 1) % len(BASES)],
                starts_at=operation_start,
                ends_at=operation_start + timedelta(days=45 + index * 3),
                mobilization_deadline=operation_start - timedelta(days=7),
                status="infeasible_demo" if index == 8 else "planning",
                budget_cents=25_000_000 + index * 3_000_000,
            )
        )
        demands.extend(
            (
                RoleDemandSeed(operation_code, roles[52 + index].code, 4 + index, "day", 10),
                RoleDemandSeed(
                    operation_code,
                    roles[-1].code if index == 8 else roles[60 + index].code,
                    75 if index == 8 else 3 + index // 2,
                    "day",
                    20,
                ),
            )
        )
    return tuple(operations), tuple(demands)


def _build_assignments(
    employees: tuple[EmployeeSeed, ...],
    operations: tuple[OperationSeed, ...],
) -> tuple[EmployeeAssignmentSeed, ...]:
    operation = operations[0]
    return tuple(
        EmployeeAssignmentSeed(
            employee_number=employee.employee_number,
            operation_code=operation.code,
            starts_at=operation.starts_at - timedelta(days=5),
            ends_at=operation.starts_at + timedelta(days=20),
            status="confirmed",
        )
        for index, employee in enumerate(employees, start=1)
        if index % 11 == 0
    )


def _build_availability(
    employees: tuple[EmployeeSeed, ...],
) -> tuple[EmployeeAvailabilitySeed, ...]:
    horizon_boundaries = (
        datetime(2026, 8, 1, tzinfo=UTC),
        datetime(2026, 11, 1, tzinfo=UTC),
        datetime(2027, 2, 1, tzinfo=UTC),
        datetime(2027, 5, 1, tzinfo=UTC),
    )
    return tuple(
        EmployeeAvailabilitySeed(
            employee_number=employee.employee_number,
            starts_at=horizon_boundaries[horizon_index],
            ends_at=horizon_boundaries[horizon_index + 1],
            status=(
                "unavailable" if (employee_index * 5 + horizon_index) % 19 == 0 else "available"
            ),
        )
        for employee_index, employee in enumerate(employees, start=1)
        for horizon_index in range(3)
    )


def _build_training_sessions(
    training_catalog: tuple[TrainingSeed, ...],
) -> tuple[TrainingSessionSeed, ...]:
    first_start = datetime(2026, 8, 17, 12, tzinfo=UTC)
    return tuple(
        TrainingSessionSeed(
            code=f"SES-{index:03d}",
            training_code=training.code,
            starts_at=first_start + timedelta(days=(index - 1) * 2),
            ends_at=first_start
            + timedelta(days=(index - 1) * 2, minutes=training.duration_minutes),
            capacity=16 + index % 4 * 4,
            base_location=BASES[(index - 1) % len(BASES)],
            status="scheduled",
        )
        for index, training in enumerate(training_catalog, start=1)
    )


def _build_requirements(
    demands: tuple[RoleDemandSeed, ...],
    qualifications: tuple[QualificationSeed, ...],
) -> tuple[RequirementSeed, ...]:
    return tuple(
        RequirementSeed(
            code=f"REQ-{index:03d}",
            operation_code=demand.operation_code,
            role_code=demand.role_code,
            shift_code=demand.shift_code,
            qualification_code=qualifications[(index * 3) % len(qualifications)].code,
            allows_training=True,
        )
        for index, demand in enumerate(demands, start=1)
    )


def generate_demo_dataset(seed: int, employee_count: int) -> DemoDataset:
    if employee_count <= 0:
        raise ValueError("employee_count must be positive")

    rng = random.Random(seed)
    families, roles = _build_roles()
    qualifications = _build_qualifications()
    authorizations = _build_authorizations()
    training_catalog = _build_training_catalog(qualifications)
    employees = _build_employees(rng, roles, employee_count)
    operations, role_demands = _build_operations(roles)
    return DemoDataset(
        seed=seed,
        bases=tuple(BASES),
        role_families=families,
        canonical_roles=roles,
        role_aliases=_build_aliases(roles),
        qualifications=qualifications,
        authorizations=authorizations,
        training_catalog=training_catalog,
        employees=employees,
        employee_qualifications=_build_employee_qualifications(rng, employees, qualifications),
        employee_costs=_build_employee_costs(employees),
        operations=operations,
        role_demands=role_demands,
        employee_availability=_build_availability(employees),
        employee_assignments=_build_assignments(employees, operations),
        training_sessions=_build_training_sessions(training_catalog),
        requirements=_build_requirements(role_demands, qualifications),
    )
