from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.main import create_app
from app.operations import models as operation_models
from app.workforce import models as workforce_models


def _seed_conflicted_investment_opportunity(session, suffix: str, conflict: str) -> None:
    family = workforce_models.RoleFamily(
        code=f"INV-CON-{suffix}-FAM", name=f"Conflito {suffix}"
    )
    session.add(family)
    session.flush()
    role = workforce_models.Role(
        family_id=family.id,
        code=f"INV-CON-{suffix}-ROLE",
        name=f"Funcao {suffix}",
        active=True,
    )
    qualification = workforce_models.Qualification(
        code=f"INV-CON-{suffix}-QLF",
        name=f"Qualificacao {suffix}",
        category="seguranca",
        active=True,
    )
    session.add_all((role, qualification))
    session.flush()
    employee = workforce_models.Employee(
        employee_number=f"INV-CON-{suffix}-001",
        name=f"Pessoa {suffix}",
        canonical_role_id=role.id,
        base_location="Curitiba",
        seniority_level="pleno",
        active=True,
    )
    operation = operation_models.Operation(
        code=f"INV-CON-{suffix}-OPS",
        name=f"Operacao {suffix}",
        client_name="Cliente",
        base_location="Curitiba",
        starts_at=datetime(2099, 4, 1, tzinfo=UTC),
        ends_at=datetime(2099, 4, 30, tzinfo=UTC),
        mobilization_deadline=datetime(2099, 3, 20, tzinfo=UTC),
        status="confirmed",
        budget_cents=None,
    )
    session.add_all((employee, operation))
    session.flush()
    demand = operation_models.OperationRoleDemand(
        operation_id=operation.id,
        role_id=role.id,
        quantity=1,
        shift_code="day",
        priority=10,
    )
    run = operation_models.EligibilityRun(
        operation_id=operation.id,
        rules_version="1.0.0",
        input_hash=("1" if conflict == "assignment" else "2") * 64,
        status="completed",
        started_at=datetime(2099, 1, 1, tzinfo=UTC),
        finished_at=datetime(2099, 1, 1, 0, 0, 1, tzinfo=UTC),
        candidate_count=1,
        evaluated_count=1,
        trainable_count=1,
    )
    session.add_all((demand, run))
    session.flush()
    session.add(
        operation_models.EligibilityResult(
            eligibility_run_id=run.id,
            employee_id=employee.id,
            role_demand_id=demand.id,
            classification="TRAINABLE",
            reason_codes=["missing_qualification"],
            reasons=[],
            gaps=[{"qualification_id": str(qualification.id)}],
            required_training_ids=[],
            incremental_cost_cents=0,
        )
    )
    catalog = workforce_models.TrainingCatalog(
        code=f"INV-CON-{suffix}-TRN",
        name=f"Curso {suffix}",
        qualification_id=qualification.id,
        duration_minutes=480,
        cost_cents=40_000,
        active=True,
    )
    session.add(catalog)
    session.flush()
    target_session = workforce_models.TrainingSession(
        training_catalog_id=catalog.id,
        starts_at=datetime(2099, 2, 1, 9, tzinfo=UTC),
        ends_at=datetime(2099, 2, 1, 17, tzinfo=UTC),
        capacity=10,
        base_location="Curitiba",
        status="open",
    )
    session.add(target_session)
    session.flush()
    if conflict == "assignment":
        session.add(
            workforce_models.EmployeeAssignment(
                employee_id=employee.id,
                operation_id=operation.id,
                starts_at=datetime(2099, 2, 1, 8, tzinfo=UTC),
                ends_at=datetime(2099, 2, 1, 18, tzinfo=UTC),
                status="confirmed",
            )
        )
        return
    booked_qualification = workforce_models.Qualification(
        code=f"INV-CON-{suffix}-BOOKED-QLF",
        name=f"Curso reservado {suffix}",
        category="tecnica",
        active=True,
    )
    session.add(booked_qualification)
    session.flush()
    booked_catalog = workforce_models.TrainingCatalog(
        code=f"INV-CON-{suffix}-BOOKED-TRN",
        name=f"Treinamento reservado {suffix}",
        qualification_id=booked_qualification.id,
        duration_minutes=600,
        cost_cents=20_000,
        active=True,
    )
    session.add(booked_catalog)
    session.flush()
    booked_session = workforce_models.TrainingSession(
        training_catalog_id=booked_catalog.id,
        starts_at=datetime(2099, 2, 1, 8, tzinfo=UTC),
        ends_at=datetime(2099, 2, 1, 18, tzinfo=UTC),
        capacity=10,
        base_location="Curitiba",
        status="open",
    )
    session.add(booked_session)
    session.flush()
    session.add(
        workforce_models.EmployeeTrainingPlan(
            employee_id=employee.id,
            training_session_id=booked_session.id,
            operation_id=None,
            status="planned",
            due_at=booked_session.ends_at,
        )
    )


def test_investment_api_generates_only_known_gaps_completed_inside_horizon() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        family = workforce_models.RoleFamily(code="INV-FAM", name="Investimento")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="INV-ROLE",
            name="Montador estrat�gico",
            active=True,
        )
        qualification = workforce_models.Qualification(
            code="INV-QLF",
            name="Qualifica��o estrat�gica",
            category="seguran�a",
            active=True,
        )
        session.add_all((role, qualification))
        session.flush()
        employee = workforce_models.Employee(
            employee_number="INV-001",
            name="Pessoa Estrat�gica",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        operation = operation_models.Operation(
            code="INV-OPS",
            name="Opera��o futura",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2099, 4, 1, tzinfo=UTC),
            ends_at=datetime(2099, 4, 30, tzinfo=UTC),
            mobilization_deadline=datetime(2099, 3, 20, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add_all((employee, operation))
        session.flush()
        demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=2,
            shift_code="day",
            priority=10,
        )
        run = operation_models.EligibilityRun(
            operation_id=operation.id,
            rules_version="1.0.0",
            input_hash="e" * 64,
            status="completed",
            started_at=datetime(2099, 1, 1, tzinfo=UTC),
            finished_at=datetime(2099, 1, 1, 0, 0, 1, tzinfo=UTC),
            candidate_count=1,
            evaluated_count=1,
            trainable_count=1,
        )
        session.add_all((demand, run))
        session.flush()
        session.add(
            operation_models.EligibilityResult(
                eligibility_run_id=run.id,
                employee_id=employee.id,
                role_demand_id=demand.id,
                classification="TRAINABLE",
                reason_codes=["missing_qualification"],
                reasons=[],
                gaps=[{"qualification_id": str(qualification.id)}],
                required_training_ids=[],
                incremental_cost_cents=0,
            )
        )
        catalog = workforce_models.TrainingCatalog(
            code="INV-TRN",
            name="Curso estrat�gico",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        session.add(catalog)
        session.flush()
        viable_session = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2099, 2, 1, 9, tzinfo=UTC),
            ends_at=datetime(2099, 2, 1, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        outside_horizon = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2099, 5, 1, 9, tzinfo=UTC),
            ends_at=datetime(2099, 5, 1, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        session.add_all((viable_session, outside_horizon))

    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.post(
            "/training/investment-plan",
            json={
                "horizon": "2099-03-31T23:59:59Z",
                "budget_cents": 40_000,
                "weights": {"confirmed": 100, "probable": 60, "hypothetical": 30},
            },
        )
    finally:
        client.close()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cost_cents"] == 40_000
    assert payload["coverage_gain"] == 100
    assert payload["unlocked_position_count"] == 1
    assert payload["opportunity_count"] == 1
    assert payload["actions"][0]["employee_name"] == "Pessoa Estrat�gica"
    assert payload["actions"][0]["training_session_id"] == str(viable_session.id)
    assert payload["actions"][0]["benefited_operations"][0]["weight"] == 100
    engine.dispose()


def test_investment_api_does_not_book_overlapping_training_for_one_employee() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        family = workforce_models.RoleFamily(code="INV-OVL-FAM", name="Sobreposicao")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="INV-OVL-ROLE",
            name="Montador sobreposicao",
            active=True,
        )
        first_qualification = workforce_models.Qualification(
            code="INV-OVL-Q1",
            name="Qualificacao sobreposta 1",
            category="seguranca",
            active=True,
        )
        second_qualification = workforce_models.Qualification(
            code="INV-OVL-Q2",
            name="Qualificacao sobreposta 2",
            category="seguranca",
            active=True,
        )
        session.add_all((role, first_qualification, second_qualification))
        session.flush()
        employee = workforce_models.Employee(
            employee_number="INV-OVL-001",
            name="Pessoa com dois gaps",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        operation = operation_models.Operation(
            code="INV-OVL-OPS",
            name="Operacao com dois gaps",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2099, 4, 1, tzinfo=UTC),
            ends_at=datetime(2099, 4, 30, tzinfo=UTC),
            mobilization_deadline=datetime(2099, 3, 20, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add_all((employee, operation))
        session.flush()
        first_demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=1,
            shift_code="day",
            priority=10,
        )
        second_demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=1,
            shift_code="night",
            priority=10,
        )
        run = operation_models.EligibilityRun(
            operation_id=operation.id,
            rules_version="1.0.0",
            input_hash="f" * 64,
            status="completed",
            started_at=datetime(2099, 1, 1, tzinfo=UTC),
            finished_at=datetime(2099, 1, 1, 0, 0, 1, tzinfo=UTC),
            candidate_count=2,
            evaluated_count=2,
            trainable_count=2,
        )
        session.add_all((first_demand, second_demand, run))
        session.flush()
        session.add_all(
            (
                operation_models.EligibilityResult(
                    eligibility_run_id=run.id,
                    employee_id=employee.id,
                    role_demand_id=first_demand.id,
                    classification="TRAINABLE",
                    reason_codes=["missing_qualification"],
                    reasons=[],
                    gaps=[{"qualification_id": str(first_qualification.id)}],
                    required_training_ids=[],
                    incremental_cost_cents=0,
                ),
                operation_models.EligibilityResult(
                    eligibility_run_id=run.id,
                    employee_id=employee.id,
                    role_demand_id=second_demand.id,
                    classification="TRAINABLE",
                    reason_codes=["missing_qualification"],
                    reasons=[],
                    gaps=[{"qualification_id": str(second_qualification.id)}],
                    required_training_ids=[],
                    incremental_cost_cents=0,
                ),
            )
        )
        first_catalog = workforce_models.TrainingCatalog(
            code="INV-OVL-T1",
            name="Curso sobreposto 1",
            qualification_id=first_qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        second_catalog = workforce_models.TrainingCatalog(
            code="INV-OVL-T2",
            name="Curso sobreposto 2",
            qualification_id=second_qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        session.add_all((first_catalog, second_catalog))
        session.flush()
        session.add_all(
            (
                workforce_models.TrainingSession(
                    training_catalog_id=first_catalog.id,
                    starts_at=datetime(2099, 2, 1, 9, tzinfo=UTC),
                    ends_at=datetime(2099, 2, 1, 17, tzinfo=UTC),
                    capacity=10,
                    base_location="Curitiba",
                    status="open",
                ),
                workforce_models.TrainingSession(
                    training_catalog_id=second_catalog.id,
                    starts_at=datetime(2099, 2, 1, 10, tzinfo=UTC),
                    ends_at=datetime(2099, 2, 1, 18, tzinfo=UTC),
                    capacity=10,
                    base_location="Curitiba",
                    status="open",
                ),
            )
        )

    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.post(
            "/training/investment-plan",
            json={
                "horizon": "2099-03-31T23:59:59Z",
                "budget_cents": 80_000,
                "weights": {"confirmed": 100, "probable": 60, "hypothetical": 30},
            },
        )
    finally:
        client.close()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["actions"]) == 1
    assert payload["coverage_gain"] == 100
    assert payload["total_cost_cents"] == 40_000
    engine.dispose()


@pytest.mark.parametrize("conflict", ["assignment", "training"])
def test_investment_api_excludes_sessions_that_conflict_with_employee_calendar(
    conflict: str,
) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        _seed_conflicted_investment_opportunity(session, conflict.upper(), conflict)

    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.post(
            "/training/investment-plan",
            json={
                "horizon": "2099-03-31T23:59:59Z",
                "budget_cents": 40_000,
                "weights": {"confirmed": 100, "probable": 60, "hypothetical": 30},
            },
        )
    finally:
        client.close()

    assert response.status_code == 200
    payload = response.json()
    assert payload["actions"] == []
    assert payload["opportunity_count"] == 0
    assert payload["coverage_gain"] == 0
    engine.dispose()
