from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dashboard.schemas import (
    DashboardExpiry,
    DashboardOperation,
    DashboardOverview,
    DashboardRiskAlert,
    RiskSeverity,
)
from app.fragility.service import FragilityService
from app.fragility.types import FragilityCell
from app.operations.models import EligibilityRun, Operation
from app.workforce.models import (
    Employee,
    EmployeeQualification,
    EmployeeTrainingPlan,
    Qualification,
    TrainingCatalog,
    TrainingSession,
)

_SEVERITY_RANK: dict[RiskSeverity, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class DashboardService:
    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(UTC))

    def get_overview(self, horizon_days: int) -> DashboardOverview:
        now = _as_utc(self._clock())
        horizon_at = now + timedelta(days=horizon_days)
        fragility = FragilityService(self._session, clock=lambda: now).calculate(
            horizon_days
        )
        cells_by_operation: dict[UUID, list[FragilityCell]] = defaultdict(list)
        for cell in fragility.cells:
            cells_by_operation[cell.operation_id].append(cell)

        operations = tuple(
            self._session.scalars(
                select(Operation)
                .where(
                    func.coalesce(Operation.mobilization_deadline, Operation.starts_at)
                    >= now,
                    func.coalesce(Operation.mobilization_deadline, Operation.starts_at)
                    <= horizon_at,
                )
                .order_by(
                    func.coalesce(Operation.mobilization_deadline, Operation.starts_at),
                    Operation.id,
                )
            )
        )
        operation_ids = {operation.id for operation in operations}
        analyzed_operation_ids = set(
            self._session.scalars(
                select(EligibilityRun.operation_id)
                .where(
                    EligibilityRun.operation_id.in_(operation_ids),
                    EligibilityRun.status == "completed",
                )
                .distinct()
            )
        )
        upcoming_operations = [
            self._operation_view(
                operation,
                cells_by_operation[operation.id],
                analyzed=operation.id in analyzed_operation_ids,
            )
            for operation in operations
        ]

        analyzed_cells = [
            cell
            for cell in fragility.cells
            if cell.operation_id in analyzed_operation_ids
        ]
        required_positions = sum(cell.metric.required_count for cell in analyzed_cells)
        covered_positions = sum(
            min(cell.metric.required_count, cell.metric.eligible_count)
            for cell in analyzed_cells
        )
        uncovered_positions = sum(
            max(cell.metric.required_count - cell.metric.eligible_count, 0)
            for cell in analyzed_cells
        )
        risky_operation_ids = {
            cell.operation_id
            for cell in analyzed_cells
            if cell.risk.severity in {"high", "critical"}
        }
        expiries = self._expiries(now, horizon_at)

        active_employee_count = self._session.scalar(
            select(func.count()).select_from(Employee).where(Employee.active.is_(True))
        ) or 0
        planned_training_cost = self._session.scalar(
            select(func.coalesce(func.sum(TrainingCatalog.cost_cents), 0))
            .select_from(EmployeeTrainingPlan)
            .join(
                TrainingSession,
                TrainingSession.id == EmployeeTrainingPlan.training_session_id,
            )
            .join(
                TrainingCatalog,
                TrainingCatalog.id == TrainingSession.training_catalog_id,
            )
            .where(
                EmployeeTrainingPlan.status.not_in(
                    ("cancelled", "canceled", "completed")
                ),
                TrainingSession.ends_at >= now,
                TrainingSession.ends_at <= horizon_at,
            )
        ) or 0

        return DashboardOverview(
            generated_at=now,
            horizon_days=horizon_days,
            active_employee_count=active_employee_count,
            readiness_percent=(
                round(covered_positions / required_positions * 100, 1)
                if required_positions
                else None
            ),
            expiring_qualification_count=len(expiries),
            risky_operation_count=len(risky_operation_ids),
            uncovered_position_count=uncovered_positions,
            planned_training_cost_cents=int(planned_training_cost),
            upcoming_operations=upcoming_operations,
            risk_alerts=self._risk_alerts(analyzed_cells),
            expiring_qualifications=expiries[:12],
        )

    @staticmethod
    def _operation_view(
        operation: Operation,
        cells: list[FragilityCell],
        *,
        analyzed: bool,
    ) -> DashboardOperation:
        if not analyzed:
            return DashboardOperation(
                id=operation.id,
                name=operation.name,
                client_name=operation.client_name,
                status=operation.status,
                mobilization_deadline=_as_utc(
                    operation.mobilization_deadline or operation.starts_at
                ),
                severity="unknown",
                analysis_status="pending",
                readiness_percent=None,
                uncovered_position_count=0,
            )
        required = sum(cell.metric.required_count for cell in cells)
        covered = sum(
            min(cell.metric.required_count, cell.metric.eligible_count) for cell in cells
        )
        severity: RiskSeverity = max(
            (cell.risk.severity for cell in cells),
            key=lambda item: _SEVERITY_RANK[item],
            default="low",
        )
        return DashboardOperation(
            id=operation.id,
            name=operation.name,
            client_name=operation.client_name,
            status=operation.status,
            mobilization_deadline=_as_utc(
                operation.mobilization_deadline or operation.starts_at
            ),
            severity=severity,
            analysis_status="completed",
            readiness_percent=round(covered / required * 100, 1) if required else 0.0,
            uncovered_position_count=sum(
                max(cell.metric.required_count - cell.metric.eligible_count, 0)
                for cell in cells
            ),
        )

    @staticmethod
    def _risk_alerts(cells: list[FragilityCell]) -> list[DashboardRiskAlert]:
        risky_cells = [
            cell for cell in cells if cell.risk.severity in {"high", "critical"}
        ]
        risky_cells.sort(
            key=lambda cell: (
                -_SEVERITY_RANK[cell.risk.severity],
                cell.mobilization_deadline,
                str(cell.demand_id),
            )
        )
        return [
            DashboardRiskAlert(
                operation_id=cell.operation_id,
                operation_name=cell.operation_name,
                demand_id=cell.demand_id,
                role_name=cell.role_name,
                shift_code=cell.shift_code,
                severity=cell.risk.severity,
                required_count=cell.metric.required_count,
                eligible_count=cell.metric.eligible_count,
                uncovered_position_count=max(
                    cell.metric.required_count - cell.metric.eligible_count, 0
                ),
                explanation=(
                    cell.risk.explanations[0].message
                    if cell.risk.explanations
                    else "Cobertura sem redundância suficiente."
                ),
            )
            for cell in risky_cells[:12]
        ]

    def _expiries(
        self,
        now: datetime,
        horizon_at: datetime,
    ) -> list[DashboardExpiry]:
        rows = self._session.execute(
            select(EmployeeQualification, Employee, Qualification)
            .join(Employee, Employee.id == EmployeeQualification.employee_id)
            .join(
                Qualification,
                Qualification.id == EmployeeQualification.qualification_id,
            )
            .where(
                Employee.active.is_(True),
                EmployeeQualification.expires_on.is_not(None),
                EmployeeQualification.expires_on >= now.date(),
                EmployeeQualification.expires_on <= horizon_at.date(),
            )
            .order_by(EmployeeQualification.expires_on, Employee.name)
        ).all()
        return [
            DashboardExpiry(
                employee_id=employee.id,
                employee_name=employee.name,
                qualification_id=qualification.id,
                qualification_name=qualification.name,
                expires_on=employee_qualification.expires_on,
                days_remaining=(employee_qualification.expires_on - now.date()).days,
            )
            for employee_qualification, employee, qualification in rows
            if employee_qualification.expires_on is not None
        ]
