from app.eligibility.rules import (
    assess_qualifications,
    assignment_reasons,
    authorization_reasons,
    availability_reasons,
    employee_status_reasons,
    experience_reasons,
    restriction_reasons,
    role_reasons,
)
from app.eligibility.types import (
    DemandEligibilityContext,
    EligibilityResult,
    EligibilityStatus,
    EmployeeEligibilityContext,
    OperationEligibilityContext,
)


class EligibilityService:
    def evaluate(
        self,
        employee: EmployeeEligibilityContext,
        operation: OperationEligibilityContext,
        demand: DemandEligibilityContext,
    ) -> EligibilityResult:
        pre_qualification_reasons = (
            employee_status_reasons(employee)
            + role_reasons(employee, demand)
            + availability_reasons(employee, operation)
            + assignment_reasons(employee, operation)
        )
        qualification = assess_qualifications(employee, operation, demand)
        post_qualification_reasons = (
            authorization_reasons(employee, operation, demand)
            + experience_reasons(employee, demand)
            + restriction_reasons(employee, operation, demand)
        )
        reasons = pre_qualification_reasons + qualification.reasons + post_qualification_reasons
        if pre_qualification_reasons or qualification.blocked or post_qualification_reasons:
            return EligibilityResult(
                status=EligibilityStatus.INELIGIBLE,
                eligible=False,
                reasons=reasons,
                gaps=qualification.gaps,
            )

        if qualification.required_training:
            return EligibilityResult(
                status=EligibilityStatus.TRAINABLE,
                eligible=False,
                reasons=reasons,
                gaps=qualification.gaps,
                required_training=qualification.required_training,
                ready_at=qualification.ready_at,
            )

        return EligibilityResult(
            status=EligibilityStatus.ELIGIBLE,
            eligible=True,
            reasons=(),
        )
