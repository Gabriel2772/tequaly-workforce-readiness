from datetime import UTC, datetime
from uuid import uuid4

from app.eligibility.reason_codes import EligibilityReasonCode
from app.eligibility.service import EligibilityService
from app.eligibility.types import (
    AssignmentWindow,
    AuthorizationFact,
    AvailabilityWindow,
    DemandEligibilityContext,
    EligibilityStatus,
    EmployeeEligibilityContext,
    OperationalRestrictionFact,
    OperationEligibilityContext,
    QualificationFact,
    TrainingOption,
)


def test_employee_without_covering_availability_is_ineligible() -> None:
    role_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(
            AvailabilityWindow(
                starts_at=operation.starts_at,
                ends_at=datetime(2026, 10, 15, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.UNAVAILABLE_FOR_OPERATION in {
        reason.code for reason in result.reasons
    }


def test_overlapping_confirmed_assignment_is_ineligible() -> None:
    role_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        assignments=(
            AssignmentWindow(
                assignment_id=uuid4(),
                starts_at=datetime(2026, 9, 30, tzinfo=UTC),
                ends_at=datetime(2026, 10, 2, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.ASSIGNMENT_CONFLICT in {reason.code for reason in result.reasons}


def test_missing_required_authorization_is_ineligible() -> None:
    role_id = uuid4()
    authorization_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        authorizations=(AuthorizationFact(authorization_id=uuid4(), expires_on=None),),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_authorization_ids=frozenset({authorization_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.MISSING_AUTHORIZATION in {reason.code for reason in result.reasons}


def test_missing_qualification_with_training_before_deadline_is_trainable() -> None:
    role_id = uuid4()
    qualification_id = uuid4()
    training_catalog_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    completes_at = datetime(2026, 9, 19, tzinfo=UTC)
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        training_options=(
            TrainingOption(
                qualification_id=qualification_id,
                training_catalog_id=training_catalog_id,
                completes_at=completes_at,
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_qualification_ids=frozenset({qualification_id}),
        trainable_qualification_ids=frozenset({qualification_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.TRAINABLE
    assert result.eligible is False
    assert result.required_training == (training_catalog_id,)
    assert result.ready_at == completes_at
    assert result.gaps == (
        {
            "qualification_id": str(qualification_id),
            "reason_code": EligibilityReasonCode.MISSING_QUALIFICATION.value,
        },
    )


def test_training_after_mobilization_deadline_is_ineligible() -> None:
    role_id = uuid4()
    qualification_id = uuid4()
    training_catalog_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        training_options=(
            TrainingOption(
                qualification_id=qualification_id,
                training_catalog_id=training_catalog_id,
                completes_at=datetime(2026, 9, 21, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_qualification_ids=frozenset({qualification_id}),
        trainable_qualification_ids=frozenset({qualification_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert result.required_training == ()
    assert EligibilityReasonCode.TRAINING_AFTER_DEADLINE in {
        reason.code for reason in result.reasons
    }


def test_training_does_not_relax_a_non_trainable_requirement() -> None:
    role_id = uuid4()
    qualification_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        training_options=(
            TrainingOption(
                qualification_id=qualification_id,
                training_catalog_id=uuid4(),
                completes_at=datetime(2026, 9, 19, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_qualification_ids=frozenset({qualification_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert result.required_training == ()
    assert EligibilityReasonCode.MISSING_QUALIFICATION in {reason.code for reason in result.reasons}


def test_inactive_employee_is_ineligible() -> None:
    role_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=False,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.INACTIVE_EMPLOYEE in {reason.code for reason in result.reasons}
    assert result.reasons[0].message == "Colaborador inativo."


def test_incompatible_role_is_ineligible() -> None:
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=uuid4(),
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({uuid4()}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.INCOMPATIBLE_ROLE in {reason.code for reason in result.reasons}


def test_insufficient_experience_is_ineligible() -> None:
    role_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        experience_months=23,
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        minimum_experience_months=24,
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.INSUFFICIENT_EXPERIENCE in {
        reason.code for reason in result.reasons
    }


def test_applicable_hard_operational_restriction_is_ineligible() -> None:
    role_id = uuid4()
    restriction_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        restrictions=(
            OperationalRestrictionFact(
                restriction_id=restriction_id,
                starts_at=datetime(2026, 10, 15, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        applicable_restriction_ids=frozenset({restriction_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.OPERATIONAL_RESTRICTION in {
        reason.code for reason in result.reasons
    }


def test_all_satisfied_rules_return_eligible() -> None:
    role_id = uuid4()
    qualification_id = uuid4()
    authorization_id = uuid4()
    restriction_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        qualifications=(QualificationFact(qualification_id, operation.ends_at),),
        availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),),
        authorizations=(AuthorizationFact(authorization_id, None),),
        restrictions=(
            OperationalRestrictionFact(
                restriction_id=restriction_id,
                hard_constraint=False,
            ),
        ),
        experience_months=24,
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_qualification_ids=frozenset({qualification_id}),
        required_authorization_ids=frozenset({authorization_id}),
        applicable_restriction_ids=frozenset({restriction_id}),
        minimum_experience_months=24,
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.ELIGIBLE
    assert result.eligible is True
    assert result.reasons == ()
    assert result.gaps == ()


def test_qualification_expiring_before_operation_end_is_ineligible() -> None:
    qualification_id = uuid4()
    role_id = uuid4()
    operation = OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )
    employee = EmployeeEligibilityContext(
        employee_id=uuid4(),
        active=True,
        role_id=role_id,
        qualifications=(
            QualificationFact(
                qualification_id=qualification_id,
                expires_on=datetime(2026, 10, 15, tzinfo=UTC),
            ),
        ),
    )
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset({role_id}),
        required_qualification_ids=frozenset({qualification_id}),
    )

    result = EligibilityService().evaluate(employee, operation, demand)

    assert result.status is EligibilityStatus.INELIGIBLE
    assert EligibilityReasonCode.QUALIFICATION_EXPIRES_BEFORE_END in {
        reason.code for reason in result.reasons
    }
