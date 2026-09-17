from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.eligibility.reason_codes import EligibilityReasonCode
from app.eligibility.rules import (
    assess_qualifications,
    assignment_reasons,
    authorization_reasons,
    availability_reasons,
)
from app.eligibility.types import (
    AssignmentWindow,
    AuthorizationFact,
    AvailabilityWindow,
    DemandEligibilityContext,
    EmployeeEligibilityContext,
    OperationEligibilityContext,
    QualificationFact,
    TrainingOption,
)


def _operation() -> OperationEligibilityContext:
    return OperationEligibilityContext(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
    )


def _employee(**overrides: object) -> EmployeeEligibilityContext:
    values: dict[str, object] = {
        "employee_id": uuid4(),
        "active": True,
        "role_id": uuid4(),
    }
    values.update(overrides)
    return EmployeeEligibilityContext(**values)  # type: ignore[arg-type]


def test_availability_must_cover_the_complete_interval() -> None:
    operation = _operation()
    exact = _employee(availability=(AvailabilityWindow(operation.starts_at, operation.ends_at),))
    one_second_short = _employee(
        availability=(
            AvailabilityWindow(
                operation.starts_at,
                operation.ends_at - timedelta(seconds=1),
            ),
        )
    )

    assert availability_reasons(exact, operation) == ()
    assert availability_reasons(one_second_short, operation)[0].code is (
        EligibilityReasonCode.UNAVAILABLE_FOR_OPERATION
    )


def test_adjacent_available_windows_jointly_cover_the_operation() -> None:
    operation = _operation()
    employee = _employee(
        availability=(
            AvailabilityWindow(
                operation.starts_at - timedelta(days=1),
                operation.starts_at + timedelta(days=10),
            ),
            AvailabilityWindow(
                operation.starts_at + timedelta(days=10),
                operation.ends_at,
            ),
        )
    )

    assert availability_reasons(employee, operation) == ()


def test_touching_assignment_does_not_overlap_but_one_second_does() -> None:
    operation = _operation()
    touching = _employee(
        assignments=(
            AssignmentWindow(
                assignment_id=uuid4(),
                starts_at=operation.starts_at - timedelta(days=1),
                ends_at=operation.starts_at,
            ),
        )
    )
    overlapping = _employee(
        assignments=(
            AssignmentWindow(
                assignment_id=uuid4(),
                starts_at=operation.starts_at - timedelta(days=1),
                ends_at=operation.starts_at + timedelta(seconds=1),
            ),
        )
    )

    assert assignment_reasons(touching, operation) == ()
    assert assignment_reasons(overlapping, operation)[0].code is (
        EligibilityReasonCode.ASSIGNMENT_CONFLICT
    )


def test_qualification_expiry_at_end_is_valid_but_one_second_before_is_not() -> None:
    operation = _operation()
    qualification_id = uuid4()
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset(),
        required_qualification_ids=frozenset({qualification_id}),
        trainable_qualification_ids=frozenset({qualification_id}),
    )
    exact = _employee(qualifications=(QualificationFact(qualification_id, operation.ends_at),))
    early = _employee(
        qualifications=(
            QualificationFact(
                qualification_id,
                operation.ends_at - timedelta(seconds=1),
            ),
        )
    )

    assert assess_qualifications(exact, operation, demand).gaps == ()
    assert assess_qualifications(early, operation, demand).reasons[0].code is (
        EligibilityReasonCode.QUALIFICATION_EXPIRES_BEFORE_END
    )


def test_authorization_expiry_at_end_is_valid_but_one_second_before_is_not() -> None:
    operation = _operation()
    authorization_id = uuid4()
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset(),
        required_authorization_ids=frozenset({authorization_id}),
    )
    exact = _employee(authorizations=(AuthorizationFact(authorization_id, operation.ends_at),))
    early = _employee(
        authorizations=(
            AuthorizationFact(
                authorization_id,
                operation.ends_at - timedelta(seconds=1),
            ),
        )
    )

    assert authorization_reasons(exact, operation, demand) == ()
    assert authorization_reasons(early, operation, demand)[0].code is (
        EligibilityReasonCode.AUTHORIZATION_EXPIRES_BEFORE_END
    )


def test_training_at_deadline_is_viable_but_one_second_after_is_not() -> None:
    operation = _operation()
    assert operation.mobilization_deadline is not None
    qualification_id = uuid4()
    demand = DemandEligibilityContext(
        demand_id=uuid4(),
        compatible_role_ids=frozenset(),
        required_qualification_ids=frozenset({qualification_id}),
        trainable_qualification_ids=frozenset({qualification_id}),
    )
    at_deadline = _employee(
        training_options=(
            TrainingOption(qualification_id, uuid4(), operation.mobilization_deadline),
        )
    )
    after_deadline = _employee(
        training_options=(
            TrainingOption(
                qualification_id,
                uuid4(),
                operation.mobilization_deadline + timedelta(seconds=1),
            ),
        )
    )

    viable = assess_qualifications(at_deadline, operation, demand)
    late = assess_qualifications(after_deadline, operation, demand)

    assert viable.blocked is False
    assert viable.ready_at == operation.mobilization_deadline
    assert late.blocked is True
    assert late.reasons[0].code is EligibilityReasonCode.TRAINING_AFTER_DEADLINE
