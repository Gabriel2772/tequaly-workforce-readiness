from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.operations import models as operation_models  # noqa: F401
from app.workforce import models as workforce_models


def test_seed_is_idempotent() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    dataset = generate_demo_dataset(seed=42, employee_count=20)

    with Session(engine) as session:
        first = seed_demo(session, dataset)
        session.commit()
        second = seed_demo(session, dataset)
        session.commit()

        employee_count = session.scalar(select(func.count()).select_from(workforce_models.Employee))
        role_count = session.scalar(select(func.count()).select_from(workforce_models.Role))
        cost_count = session.scalar(
            select(func.count()).select_from(workforce_models.EmployeeCostProfile)
        )
        assignment_count = session.scalar(
            select(func.count()).select_from(workforce_models.EmployeeAssignment)
        )
        availability_count = session.scalar(
            select(func.count()).select_from(workforce_models.EmployeeAvailability)
        )
        training_session_count = session.scalar(
            select(func.count()).select_from(workforce_models.TrainingSession)
        )
        requirement_count = session.scalar(
            select(func.count()).select_from(operation_models.OperationRequirement)
        )
        outcome_count = session.scalar(
            select(func.count()).select_from(decision_models.DecisionOutcome)
        )
        calibration_parameter_count = session.scalar(
            select(func.count()).select_from(decision_models.CalibrationParameter)
        )
        user_count = session.scalar(select(func.count()).select_from(auth_models.AppUser))

    assert first == second
    assert employee_count == 20
    assert role_count == 90
    assert cost_count == 20
    assert assignment_count == 1
    assert availability_count == 60
    assert training_session_count == 24
    assert requirement_count == 16
    assert outcome_count == 5
    assert calibration_parameter_count == 1
    assert user_count == 3
    engine.dispose()


def test_reseed_uses_batched_upserts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    dataset = generate_demo_dataset(seed=42, employee_count=20)
    statement_count = 0

    @event.listens_for(engine, "before_cursor_execute")
    def count_statements(*_args: object) -> None:
        nonlocal statement_count
        statement_count += 1

    with Session(engine) as session:
        seed_demo(session, dataset)
        session.commit()
        statement_count = 0

        seed_demo(session, dataset)
        session.commit()

    assert statement_count <= 40
    engine.dispose()


def test_main_2_200_person_seed_can_run_twice_without_duplicates() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    dataset = generate_demo_dataset(seed=42, employee_count=2_200)

    with Session(engine) as session:
        seed_demo(session, dataset)
        session.commit()
        seed_demo(session, dataset)
        session.commit()

        employee_count = session.scalar(select(func.count()).select_from(workforce_models.Employee))
        qualification_link_count = session.scalar(
            select(func.count()).select_from(workforce_models.EmployeeQualification)
        )

    assert employee_count == 2_200
    assert qualification_link_count == len(dataset.employee_qualifications)
    engine.dispose()
