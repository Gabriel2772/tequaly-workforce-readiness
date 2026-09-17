from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

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
    EmployeeTrainingPlan,
    OperationalRestriction,
    Qualification,
    Role,
    TechnicalCompetency,
    TrainingCatalog,
    TrainingSession,
)
from app.workforce.schemas import EmployeeListItem, PaginatedEmployees


@dataclass(frozen=True)
class QualificationSource:
    id: UUID
    name: str
    category: str
    issued_on: date
    expires_on: date | None


@dataclass(frozen=True)
class CompetencySource:
    name: str
    level: int
    assessed_on: date


@dataclass(frozen=True)
class AuthorizationSource:
    name: str
    scope: str | None
    issued_on: date
    expires_on: date | None


@dataclass(frozen=True)
class AvailabilitySource:
    starts_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True)
class AssignmentSource:
    operation_name: str
    starts_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True)
class CostSource:
    currency: str
    hourly_cost_cents: int
    travel_cost_cents: int
    effective_from: date


@dataclass(frozen=True)
class TrainingSource:
    training_name: str
    starts_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True)
class RestrictionSource:
    restriction_name: str
    scope: str | None
    starts_at: datetime | None
    ends_at: datetime | None


@dataclass(frozen=True)
class EmployeeProfileSource:
    role_name: str
    name: str
    base_location: str
    seniority_level: str
    updated_at: datetime
    qualifications: tuple[QualificationSource, ...] = ()
    competencies: tuple[CompetencySource, ...] = ()
    authorizations: tuple[AuthorizationSource, ...] = ()
    availability: tuple[AvailabilitySource, ...] = ()
    assignments: tuple[AssignmentSource, ...] = ()
    costs: tuple[CostSource, ...] = ()
    training: tuple[TrainingSource, ...] = ()
    restrictions: tuple[RestrictionSource, ...] = ()


class ProfileRepository(Protocol):
    def get_profile_source(self, employee_id: UUID) -> EmployeeProfileSource | None: ...


@dataclass(frozen=True)
class EmployeeListFilters:
    query: str | None = None
    role_id: UUID | None = None
    qualification_id: UUID | None = None
    status: str | None = None
    base_id: str | None = None
    available_from: datetime | None = None
    available_to: datetime | None = None


class SQLAlchemyEmployeeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_employees(
        self,
        filters: EmployeeListFilters,
        *,
        page: int,
        page_size: int,
    ) -> PaginatedEmployees:
        conditions = []
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            conditions.append(
                or_(Employee.name.ilike(pattern), Employee.employee_number.ilike(pattern))
            )
        if filters.role_id:
            conditions.append(Employee.canonical_role_id == filters.role_id)
        if filters.status in {"active", "ativo"}:
            conditions.append(Employee.active.is_(True))
        elif filters.status in {"inactive", "inativo"}:
            conditions.append(Employee.active.is_(False))
        if filters.base_id:
            conditions.append(Employee.base_location == filters.base_id)
        if filters.qualification_id:
            conditions.append(
                select(EmployeeQualification.id)
                .where(
                    EmployeeQualification.employee_id == Employee.id,
                    EmployeeQualification.qualification_id == filters.qualification_id,
                )
                .exists()
            )
        if filters.available_from and filters.available_to:
            conditions.append(
                select(EmployeeAvailability.id)
                .where(
                    EmployeeAvailability.employee_id == Employee.id,
                    EmployeeAvailability.starts_at <= filters.available_from,
                    EmployeeAvailability.ends_at >= filters.available_to,
                    EmployeeAvailability.status == "available",
                )
                .exists()
            )

        total = self._session.scalar(select(func.count()).select_from(Employee).where(*conditions))
        rows = self._session.execute(
            select(Employee, Role.name.label("role_name"))
            .join(Role, Role.id == Employee.canonical_role_id)
            .where(*conditions)
            .order_by(Employee.name, Employee.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return PaginatedEmployees(
            items=[
                EmployeeListItem(
                    id=employee.id,
                    employee_number=employee.employee_number,
                    name=employee.name,
                    role_name=role_name,
                    base_location=employee.base_location,
                    seniority_level=employee.seniority_level,
                    active=employee.active,
                    updated_at=employee.updated_at,
                )
                for employee, role_name in rows
            ],
            page=page,
            page_size=page_size,
            total=total or 0,
        )

    def get_profile_source(self, employee_id: UUID) -> EmployeeProfileSource | None:
        core = self._session.execute(
            select(Employee, Role.name.label("role_name"))
            .join(Role, Role.id == Employee.canonical_role_id)
            .where(Employee.id == employee_id)
        ).one_or_none()
        if core is None:
            return None
        employee, role_name = core

        qualifications = tuple(
            QualificationSource(
                id=qualification.id,
                name=qualification.name,
                category=qualification.category,
                issued_on=link.issued_on,
                expires_on=link.expires_on,
            )
            for link, qualification in self._session.execute(
                select(EmployeeQualification, Qualification)
                .join(
                    Qualification,
                    Qualification.id == EmployeeQualification.qualification_id,
                )
                .where(EmployeeQualification.employee_id == employee_id)
                .order_by(Qualification.name)
            ).all()
        )
        competencies = tuple(
            CompetencySource(
                name=competency.name,
                level=link.level,
                assessed_on=link.assessed_on,
            )
            for link, competency in self._session.execute(
                select(EmployeeCompetency, TechnicalCompetency)
                .join(
                    TechnicalCompetency,
                    TechnicalCompetency.id == EmployeeCompetency.competency_id,
                )
                .where(EmployeeCompetency.employee_id == employee_id)
                .order_by(TechnicalCompetency.name)
            ).all()
        )
        authorizations = tuple(
            AuthorizationSource(
                name=authorization.name,
                scope=link.scope_value,
                issued_on=link.issued_on,
                expires_on=link.expires_on,
            )
            for link, authorization in self._session.execute(
                select(EmployeeAuthorization, Authorization)
                .join(
                    Authorization,
                    Authorization.id == EmployeeAuthorization.authorization_id,
                )
                .where(EmployeeAuthorization.employee_id == employee_id)
                .order_by(Authorization.name)
            ).all()
        )
        availability = tuple(
            AvailabilitySource(row.starts_at, row.ends_at, row.status)
            for row in self._session.scalars(
                select(EmployeeAvailability)
                .where(EmployeeAvailability.employee_id == employee_id)
                .order_by(EmployeeAvailability.starts_at)
            )
        )
        assignments = tuple(
            AssignmentSource(operation.name, link.starts_at, link.ends_at, link.status)
            for link, operation in self._session.execute(
                select(EmployeeAssignment, Operation)
                .join(Operation, Operation.id == EmployeeAssignment.operation_id)
                .where(EmployeeAssignment.employee_id == employee_id)
                .order_by(EmployeeAssignment.starts_at)
            ).all()
        )
        costs = tuple(
            CostSource(
                row.currency,
                row.hourly_cost_cents,
                row.travel_cost_cents,
                row.effective_from,
            )
            for row in self._session.scalars(
                select(EmployeeCostProfile)
                .where(EmployeeCostProfile.employee_id == employee_id)
                .order_by(EmployeeCostProfile.effective_from.desc())
            )
        )
        training = tuple(
            TrainingSource(catalog.name, session.starts_at, session.ends_at, plan.status)
            for plan, session, catalog in self._session.execute(
                select(EmployeeTrainingPlan, TrainingSession, TrainingCatalog)
                .join(
                    TrainingSession,
                    TrainingSession.id == EmployeeTrainingPlan.training_session_id,
                )
                .join(
                    TrainingCatalog,
                    TrainingCatalog.id == TrainingSession.training_catalog_id,
                )
                .where(EmployeeTrainingPlan.employee_id == employee_id)
                .order_by(TrainingSession.starts_at)
            ).all()
        )
        restrictions = tuple(
            RestrictionSource(
                restriction.name,
                link.scope_value,
                link.starts_at,
                link.ends_at,
            )
            for link, restriction in self._session.execute(
                select(EmployeeOperationalRestriction, OperationalRestriction)
                .join(
                    OperationalRestriction,
                    OperationalRestriction.id == EmployeeOperationalRestriction.restriction_id,
                )
                .where(EmployeeOperationalRestriction.employee_id == employee_id)
                .order_by(OperationalRestriction.name)
            ).all()
        )
        return EmployeeProfileSource(
            role_name=role_name,
            name=employee.name,
            base_location=employee.base_location,
            seniority_level=employee.seniority_level,
            updated_at=employee.updated_at,
            qualifications=qualifications,
            competencies=competencies,
            authorizations=authorizations,
            availability=availability,
            assignments=assignments,
            costs=costs,
            training=training,
            restrictions=restrictions,
        )
