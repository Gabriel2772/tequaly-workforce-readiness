from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decisions.models import AuditEvent
from app.eligibility import ELIGIBILITY_RULES_VERSION
from app.eligibility.candidate_pool import CandidatePoolBuilder
from app.eligibility.schemas import (
    CandidateEligibilityView,
    EligibilityReasonView,
    EligibilityRunView,
)
from app.eligibility.service import EligibilityService
from app.eligibility.types import EligibilityStatus
from app.operations.models import (
    EligibilityResult as PersistedEligibilityResult,
)
from app.operations.models import EligibilityRun


class EligibilityRunNotFoundError(LookupError):
    pass


class EligibilityRunQueryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_latest(self, operation_id: UUID) -> EligibilityRunView:
        run = self._session.scalar(
            select(EligibilityRun)
            .where(
                EligibilityRun.operation_id == operation_id,
                EligibilityRun.status == "completed",
            )
            .order_by(EligibilityRun.finished_at.desc(), EligibilityRun.id.desc())
            .limit(1)
        )
        if run is None or run.finished_at is None:
            raise EligibilityRunNotFoundError(str(operation_id))
        results = tuple(
            self._session.scalars(
                select(PersistedEligibilityResult)
                .where(PersistedEligibilityResult.eligibility_run_id == run.id)
                .order_by(
                    PersistedEligibilityResult.role_demand_id,
                    PersistedEligibilityResult.employee_id,
                )
            )
        )
        return EligibilityRunView(
            id=run.id,
            operation_id=operation_id,
            rules_version=run.rules_version,
            input_hash=run.input_hash,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            runtime_ms=run.runtime_ms or 0,
            candidate_count=run.candidate_count,
            evaluated_count=run.evaluated_count,
            eligible_count=run.eligible_count,
            trainable_count=run.trainable_count,
            ineligible_count=run.ineligible_count,
            results=[
                CandidateEligibilityView(
                    employee_id=result.employee_id,
                    demand_id=result.role_demand_id,
                    classification=EligibilityStatus(result.classification),
                    reasons=[
                        EligibilityReasonView.model_validate(reason)
                        for reason in result.reasons
                    ],
                    gaps=result.gaps,
                    required_training=[
                        UUID(training_id)
                        for training_id in result.required_training_ids
                    ],
                    ready_at=result.ready_at,
                )
                for result in results
            ],
        )


class EligibilityRunService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def run_operation(self, operation_id: UUID) -> EligibilityRunView:
        timer_started = perf_counter()
        started_at = datetime.now(UTC)
        pool = CandidatePoolBuilder(self._session).build(operation_id)
        run = EligibilityRun(
            operation_id=operation_id,
            rules_version=ELIGIBILITY_RULES_VERSION,
            input_hash=pool.input_hash,
            status="running",
            started_at=started_at,
            finished_at=None,
            candidate_count=pool.candidate_count,
            evaluated_count=pool.evaluated_count,
            eligible_count=0,
            trainable_count=0,
            ineligible_count=0,
            runtime_ms=None,
        )
        self._session.add(run)
        self._session.flush()

        evaluator = EligibilityService()
        views: list[CandidateEligibilityView] = []
        counts = {status: 0 for status in EligibilityStatus}
        for demand in pool.demands:
            for employee in demand.employees:
                result = evaluator.evaluate(employee, pool.operation, demand.context)
                counts[result.status] += 1
                reasons = [
                    {
                        "code": reason.code.value,
                        "message": reason.message,
                        "details": reason.details,
                    }
                    for reason in result.reasons
                ]
                self._session.add(
                    PersistedEligibilityResult(
                        eligibility_run_id=run.id,
                        employee_id=employee.employee_id,
                        role_demand_id=demand.demand_id,
                        classification=result.status.value,
                        reason_codes=[reason.code.value for reason in result.reasons],
                        reasons=reasons,
                        gaps=list(result.gaps),
                        required_training_ids=[
                            str(training_id) for training_id in result.required_training
                        ],
                        ready_at=result.ready_at,
                        incremental_cost_cents=0,
                    )
                )
                views.append(
                    CandidateEligibilityView(
                        employee_id=employee.employee_id,
                        demand_id=demand.demand_id,
                        classification=result.status,
                        reasons=[
                            EligibilityReasonView.model_validate(reason) for reason in reasons
                        ],
                        gaps=list(result.gaps),
                        required_training=list(result.required_training),
                        ready_at=result.ready_at,
                    )
                )

        finished_at = datetime.now(UTC)
        runtime_ms = max(0, round((perf_counter() - timer_started) * 1000))
        run.status = "completed"
        run.finished_at = finished_at
        run.runtime_ms = runtime_ms
        run.eligible_count = counts[EligibilityStatus.ELIGIBLE]
        run.trainable_count = counts[EligibilityStatus.TRAINABLE]
        run.ineligible_count = counts[EligibilityStatus.INELIGIBLE]
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="eligibility.run_completed",
                aggregate_type="operation",
                aggregate_id=operation_id,
                payload={
                    "eligibility_run_id": str(run.id),
                    "rules_version": ELIGIBILITY_RULES_VERSION,
                    "candidate_count": run.candidate_count,
                    "evaluated_count": run.evaluated_count,
                    "prefiltered_from": pool.total_active_employees,
                    "eligible_count": run.eligible_count,
                    "trainable_count": run.trainable_count,
                    "ineligible_count": run.ineligible_count,
                    "runtime_ms": runtime_ms,
                },
                occurred_at=finished_at,
            )
        )
        self._session.flush()
        return EligibilityRunView(
            id=run.id,
            operation_id=operation_id,
            rules_version=run.rules_version,
            input_hash=run.input_hash,
            status=run.status,
            started_at=started_at,
            finished_at=finished_at,
            runtime_ms=runtime_ms,
            candidate_count=run.candidate_count,
            evaluated_count=run.evaluated_count,
            eligible_count=run.eligible_count,
            trainable_count=run.trainable_count,
            ineligible_count=run.ineligible_count,
            results=views,
        )
