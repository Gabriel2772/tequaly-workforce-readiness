from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.eligibility.reason_codes import EligibilityReasonCode
from app.eligibility.types import (
    DemandEligibilityContext,
    EligibilityReason,
    EmployeeEligibilityContext,
    OperationEligibilityContext,
)


def employee_status_reasons(
    employee: EmployeeEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    if employee.active:
        return ()
    return (
        EligibilityReason(
            code=EligibilityReasonCode.INACTIVE_EMPLOYEE,
            details={"employee_id": str(employee.employee_id)},
        ),
    )


def role_reasons(
    employee: EmployeeEligibilityContext,
    demand: DemandEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    if employee.role_id in demand.compatible_role_ids:
        return ()
    return (
        EligibilityReason(
            code=EligibilityReasonCode.INCOMPATIBLE_ROLE,
            details={
                "employee_role_id": str(employee.role_id),
                "demand_id": str(demand.demand_id),
            },
        ),
    )


def availability_reasons(
    employee: EmployeeEligibilityContext,
    operation: OperationEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    available_windows = sorted(
        (
            window
            for window in employee.availability
            if window.status.casefold() == "available"
            and window.ends_at > operation.starts_at
            and window.starts_at < operation.ends_at
        ),
        key=lambda window: (window.starts_at, window.ends_at),
    )
    covered_until = operation.starts_at
    for window in available_windows:
        if window.starts_at > covered_until:
            break
        if window.ends_at > covered_until:
            covered_until = window.ends_at
        if covered_until >= operation.ends_at:
            return ()

    return (
        EligibilityReason(
            code=EligibilityReasonCode.UNAVAILABLE_FOR_OPERATION,
            details={
                "starts_at": operation.starts_at.isoformat(),
                "ends_at": operation.ends_at.isoformat(),
            },
        ),
    )


def assignment_reasons(
    employee: EmployeeEligibilityContext,
    operation: OperationEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    inactive_statuses = {"cancelled", "canceled", "completed"}
    conflicts = sorted(
        (
            assignment
            for assignment in employee.assignments
            if assignment.status.casefold() not in inactive_statuses
            and assignment.starts_at < operation.ends_at
            and assignment.ends_at > operation.starts_at
        ),
        key=lambda assignment: (assignment.starts_at, str(assignment.assignment_id)),
    )
    return tuple(
        EligibilityReason(
            code=EligibilityReasonCode.ASSIGNMENT_CONFLICT,
            details={
                "assignment_id": str(conflict.assignment_id),
                "starts_at": conflict.starts_at.isoformat(),
                "ends_at": conflict.ends_at.isoformat(),
            },
        )
        for conflict in conflicts
    )


def authorization_reasons(
    employee: EmployeeEligibilityContext,
    operation: OperationEligibilityContext,
    demand: DemandEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    authorizations = {
        authorization.authorization_id: authorization for authorization in employee.authorizations
    }
    reasons: list[EligibilityReason] = []
    for authorization_id in sorted(demand.required_authorization_ids, key=str):
        authorization = authorizations.get(authorization_id)
        if authorization is None:
            reasons.append(
                EligibilityReason(
                    code=EligibilityReasonCode.MISSING_AUTHORIZATION,
                    details={"authorization_id": str(authorization_id)},
                )
            )
        elif authorization.expires_on is not None and authorization.expires_on < operation.ends_at:
            reasons.append(
                EligibilityReason(
                    code=EligibilityReasonCode.AUTHORIZATION_EXPIRES_BEFORE_END,
                    details={
                        "authorization_id": str(authorization_id),
                        "expires_on": authorization.expires_on.isoformat(),
                    },
                )
            )
    return tuple(reasons)


def experience_reasons(
    employee: EmployeeEligibilityContext,
    demand: DemandEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    if employee.experience_months >= demand.minimum_experience_months:
        return ()
    return (
        EligibilityReason(
            code=EligibilityReasonCode.INSUFFICIENT_EXPERIENCE,
            details={
                "actual_months": employee.experience_months,
                "required_months": demand.minimum_experience_months,
            },
        ),
    )


def restriction_reasons(
    employee: EmployeeEligibilityContext,
    operation: OperationEligibilityContext,
    demand: DemandEligibilityContext,
) -> tuple[EligibilityReason, ...]:
    applicable = sorted(
        (
            restriction
            for restriction in employee.restrictions
            if restriction.hard_constraint
            and restriction.restriction_id in demand.applicable_restriction_ids
            and (restriction.starts_at is None or restriction.starts_at < operation.ends_at)
            and (restriction.ends_at is None or restriction.ends_at > operation.starts_at)
        ),
        key=lambda restriction: str(restriction.restriction_id),
    )
    return tuple(
        EligibilityReason(
            code=EligibilityReasonCode.OPERATIONAL_RESTRICTION,
            details={
                "restriction_id": str(restriction.restriction_id),
                "scope_value": restriction.scope_value,
            },
        )
        for restriction in applicable
    )


@dataclass(frozen=True)
class QualificationAssessment:
    reasons: tuple[EligibilityReason, ...]
    gaps: tuple[dict[str, object], ...]
    required_training: tuple[UUID, ...]
    ready_at: datetime | None
    blocked: bool


def assess_qualifications(
    employee: EmployeeEligibilityContext,
    operation: OperationEligibilityContext,
    demand: DemandEligibilityContext,
) -> QualificationAssessment:
    qualifications = {
        qualification.qualification_id: qualification for qualification in employee.qualifications
    }
    reasons: list[EligibilityReason] = []
    gaps: list[dict[str, object]] = []
    required_training: list[UUID] = []
    ready_at: datetime | None = None
    blocked = False
    deadline = operation.mobilization_deadline or operation.starts_at

    for qualification_id in sorted(demand.required_qualification_ids, key=str):
        qualification = qualifications.get(qualification_id)
        reason_code: EligibilityReasonCode | None = None
        details: dict[str, object] = {"qualification_id": str(qualification_id)}
        if qualification is None:
            reason_code = EligibilityReasonCode.MISSING_QUALIFICATION
        elif qualification.expires_on is not None and qualification.expires_on < operation.ends_at:
            reason_code = EligibilityReasonCode.QUALIFICATION_EXPIRES_BEFORE_END
            details["expires_on"] = qualification.expires_on.isoformat()

        if reason_code is None:
            continue

        gaps.append(
            {
                "qualification_id": str(qualification_id),
                "reason_code": reason_code.value,
            }
        )
        options = (
            sorted(
                (
                    option
                    for option in employee.training_options
                    if option.qualification_id == qualification_id
                ),
                key=lambda option: (option.completes_at, str(option.training_catalog_id)),
            )
            if qualification_id in demand.trainable_qualification_ids
            else []
        )
        viable_options = [option for option in options if option.completes_at <= deadline]
        if viable_options:
            selected = viable_options[0]
            required_training.append(selected.training_catalog_id)
            ready_at = max(ready_at, selected.completes_at) if ready_at else selected.completes_at
            reasons.append(EligibilityReason(code=reason_code, details=details))
            continue

        blocked = True
        if options:
            earliest = options[0]
            reasons.append(
                EligibilityReason(
                    code=EligibilityReasonCode.TRAINING_AFTER_DEADLINE,
                    details={
                        **details,
                        "training_catalog_id": str(earliest.training_catalog_id),
                        "completes_at": earliest.completes_at.isoformat(),
                        "deadline": deadline.isoformat(),
                    },
                )
            )
        else:
            reasons.append(EligibilityReason(code=reason_code, details=details))

    return QualificationAssessment(
        reasons=tuple(reasons),
        gaps=tuple(gaps),
        required_training=tuple(required_training),
        ready_at=ready_at,
        blocked=blocked,
    )
