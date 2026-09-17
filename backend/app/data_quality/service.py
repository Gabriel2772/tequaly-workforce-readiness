from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.data_quality.schemas import DataQualityIssue, DataQualityOverview
from app.operations.models import EligibilityRun, Operation
from app.workforce.models import Employee, EmployeeCostProfile, EmployeeQualification


class DataQualityService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def overview(self) -> DataQualityOverview:
        today = datetime.now(UTC).date()
        active_filter = Employee.active.is_(True)
        active_count = self._count(select(Employee.id).where(active_filter))
        incomplete_profile = self._count(
            select(Employee.id).where(
                active_filter,
                (
                    Employee.email.is_(None)
                    | (Employee.email == "")
                    | Employee.hired_on.is_(None)
                    | (Employee.base_location == "")
                    | (Employee.seniority_level == "")
                ),
            )
        )
        without_qualification = self._count(
            select(Employee.id).where(
                active_filter,
                ~exists().where(EmployeeQualification.employee_id == Employee.id),
            )
        )
        with_expired_qualification = self._count(
            select(EmployeeQualification.employee_id)
            .join(Employee, Employee.id == EmployeeQualification.employee_id)
            .where(active_filter, EmployeeQualification.expires_on < today)
            .distinct()
        )
        without_cost = self._count(
            select(Employee.id).where(
                active_filter,
                ~exists().where(EmployeeCostProfile.employee_id == Employee.id),
            )
        )
        operations_without_analysis = self._count(
            select(Operation.id).where(
                Operation.status.not_in(("completed", "cancelled", "canceled")),
                ~exists().where(
                    EligibilityRun.operation_id == Operation.id,
                    EligibilityRun.status == "completed",
                ),
            )
        )
        complete_profiles = max(active_count - incomplete_profile, 0)
        issues = [
            DataQualityIssue(
                code="incomplete_employee_profile",
                label="Perfis ativos incompletos",
                count=incomplete_profile,
                severity="high" if incomplete_profile else "low",
                action="Completar e-mail, admissão, base e senioridade.",
            ),
            DataQualityIssue(
                code="employee_without_qualification",
                label="Pessoas sem qualificação registrada",
                count=without_qualification,
                severity="high" if without_qualification else "low",
                action="Confirmar a origem cadastral antes de planejar mobilização.",
            ),
            DataQualityIssue(
                code="expired_qualification",
                label="Pessoas com qualificação vencida",
                count=with_expired_qualification,
                severity="medium" if with_expired_qualification else "low",
                action="Atualizar validade ou programar reciclagem.",
            ),
            DataQualityIssue(
                code="employee_without_cost",
                label="Pessoas sem perfil de custo",
                count=without_cost,
                severity="medium" if without_cost else "low",
                action="Completar custos antes de comparar cenários.",
            ),
            DataQualityIssue(
                code="operation_without_eligibility",
                label="Operações sem análise de elegibilidade",
                count=operations_without_analysis,
                severity="medium" if operations_without_analysis else "low",
                action="Executar elegibilidade para evitar cobertura desconhecida.",
            ),
        ]
        return DataQualityOverview(
            active_employees=active_count,
            complete_profiles=complete_profiles,
            completeness_percent=(
                round(complete_profiles / active_count * 100, 2) if active_count else None
            ),
            issues=issues,
            source_mode="synthetic_demo",
        )

    def _count(self, query: Select[tuple[UUID]]) -> int:
        subquery = query.subquery()
        return int(self._session.scalar(select(func.count()).select_from(subquery)) or 0)
