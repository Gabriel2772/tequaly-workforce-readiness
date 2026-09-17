from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.operations import models as operation_models
from app.training.operation_service import TrainingPlanningService
from app.workforce import models as workforce_models


def _add_trainable_gap(session: Session, suffix: str = "BLOCK") -> tuple[
    operation_models.Operation,
    workforce_models.Employee,
    workforce_models.Qualification,
]:
    family = workforce_models.RoleFamily(code=f"FAM-{suffix}", name=f"Família {suffix}")
    session.add(family)
    session.flush()
    role = workforce_models.Role(
        family_id=family.id,
        code=f"ROLE-{suffix}",
        name=f"Montador {suffix}",
        active=True,
    )
    qualification = workforce_models.Qualification(
        code=f"QLF-{suffix}",
        name=f"Qualificação {suffix}",
        category="segurança",
        active=True,
    )
    session.add_all((role, qualification))
    session.flush()
    employee = workforce_models.Employee(
        employee_number=f"EMP-{suffix}",
        name=f"Pessoa {suffix}",
        canonical_role_id=role.id,
        base_location="Curitiba",
        seniority_level="pleno",
        active=True,
    )
    operation = operation_models.Operation(
        code=f"OPS-{suffix}",
        name=f"Operação {suffix}",
        client_name="Cliente Teste",
        base_location="Curitiba",
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        status="planning",
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
        input_hash="b" * 64,
        status="completed",
        started_at=datetime(2026, 8, 1, tzinfo=UTC),
        finished_at=datetime(2026, 8, 1, 0, 0, 1, tzinfo=UTC),
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
    session.flush()
    return operation, employee, qualification


def test_trainable_gap_chooses_earliest_session_before_mobilization_deadline() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="FAM-TRN", name="Família Capacitação")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="ROLE-TRN",
            name="Montador de Capacitação",
            active=True,
        )
        qualification = workforce_models.Qualification(
            code="QLF-TRN",
            name="NR de Capacitação",
            category="segurança",
            active=True,
        )
        session.add_all((role, qualification))
        session.flush()
        employee = workforce_models.Employee(
            employee_number="TRN-001",
            name="Pessoa Treinável",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        mobilization_deadline = datetime(2026, 9, 20, tzinfo=UTC)
        operation = operation_models.Operation(
            code="OPS-TRN-001",
            name="Operação de Capacitação",
            client_name="Cliente Teste",
            base_location="Curitiba",
            starts_at=datetime(2026, 10, 1, tzinfo=UTC),
            ends_at=datetime(2026, 10, 31, tzinfo=UTC),
            mobilization_deadline=mobilization_deadline,
            status="planning",
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
            input_hash="a" * 64,
            status="completed",
            started_at=datetime(2026, 8, 1, tzinfo=UTC),
            finished_at=datetime(2026, 8, 1, 0, 0, 1, tzinfo=UTC),
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
                gaps=[
                    {
                        "qualification_id": str(qualification.id),
                        "reason_code": "missing_qualification",
                    }
                ],
                required_training_ids=[],
                incremental_cost_cents=0,
            )
        )
        expensive = workforce_models.TrainingCatalog(
            code="TRN-EXP",
            name="Curso Caro",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=90_000,
            active=True,
        )
        cheaper = workforce_models.TrainingCatalog(
            code="TRN-CHEAP",
            name="Curso Econômico",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=50_000,
            active=True,
        )
        session.add_all((expensive, cheaper))
        session.flush()
        expected_completion = datetime(2026, 9, 10, 17, tzinfo=UTC)
        session.add_all(
            (
                workforce_models.TrainingSession(
                    training_catalog_id=expensive.id,
                    starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                    ends_at=expected_completion,
                    capacity=10,
                    base_location="Curitiba",
                    status="open",
                ),
                workforce_models.TrainingSession(
                    training_catalog_id=cheaper.id,
                    starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                    ends_at=expected_completion,
                    capacity=10,
                    base_location="Curitiba",
                    status="scheduled",
                ),
                workforce_models.TrainingSession(
                    training_catalog_id=cheaper.id,
                    starts_at=datetime(2026, 9, 21, 9, tzinfo=UTC),
                    ends_at=datetime(2026, 9, 21, 17, tzinfo=UTC),
                    capacity=10,
                    base_location="Curitiba",
                    status="scheduled",
                ),
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.employee_id == employee.id
    assert action.training_catalog_id == cheaper.id
    assert action.completes_at == expected_completion
    assert action.completes_at <= mobilization_deadline
    assert action.cost_cents == 50_000
    assert plan.blockers == []
    engine.dispose()


def test_trainable_gap_without_viable_session_is_reported_as_blocked() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, employee, qualification = _add_trainable_gap(session)
        session.add(
            workforce_models.TrainingCatalog(
                code="TRN-BLOCK",
                name="Curso sem turma viável",
                qualification_id=qualification.id,
                duration_minutes=480,
                cost_cents=40_000,
                active=True,
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert plan.actions == []
    assert len(plan.blockers) == 1
    blocker = plan.blockers[0]
    assert blocker.employee_id == employee.id
    assert blocker.qualification_id == qualification.id
    assert blocker.code == "no_session_before_deadline"
    assert "mobilização" in blocker.message
    engine.dispose()


def test_training_plan_never_overbooks_session_capacity() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, _, qualification = _add_trainable_gap(session, "CAP")
        first_employee = session.scalar(
            select(workforce_models.Employee).where(
                workforce_models.Employee.employee_number == "EMP-CAP"
            )
        )
        assert first_employee is not None
        second_employee = workforce_models.Employee(
            employee_number="EMP-CAP-002",
            name="Pessoa Capacidade 2",
            canonical_role_id=first_employee.canonical_role_id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        session.add(second_employee)
        session.flush()
        run = session.scalar(
            select(operation_models.EligibilityRun).where(
                operation_models.EligibilityRun.operation_id == operation.id
            )
        )
        demand = session.scalar(
            select(operation_models.OperationRoleDemand).where(
                operation_models.OperationRoleDemand.operation_id == operation.id
            )
        )
        assert run is not None and demand is not None
        session.add(
            operation_models.EligibilityResult(
                eligibility_run_id=run.id,
                employee_id=second_employee.id,
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
            code="TRN-CAP",
            name="Curso com uma vaga",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        session.add(catalog)
        session.flush()
        session.add(
            workforce_models.TrainingSession(
                training_catalog_id=catalog.id,
                starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                ends_at=datetime(2026, 9, 10, 17, tzinfo=UTC),
                capacity=1,
                base_location="Curitiba",
                status="open",
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert len(plan.actions) == 1
    assert len(plan.blockers) == 1
    assert plan.blockers[0].code == "no_session_before_deadline"
    engine.dispose()


def test_training_plan_skips_session_that_overlaps_employee_assignment() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, employee, qualification = _add_trainable_gap(session, "CONFLICT")
        catalog = workforce_models.TrainingCatalog(
            code="TRN-CONFLICT",
            name="Curso com alternativa",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        session.add(catalog)
        session.flush()
        conflicting_session = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
            ends_at=datetime(2026, 9, 10, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        compatible_session = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2026, 9, 11, 9, tzinfo=UTC),
            ends_at=datetime(2026, 9, 11, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        session.add_all((conflicting_session, compatible_session))
        session.flush()
        session.add(
            workforce_models.EmployeeAssignment(
                employee_id=employee.id,
                operation_id=operation.id,
                starts_at=datetime(2026, 9, 10, 8, tzinfo=UTC),
                ends_at=datetime(2026, 9, 10, 18, tzinfo=UTC),
                status="confirmed",
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert len(plan.actions) == 1
    assert plan.actions[0].training_session_id == compatible_session.id
    engine.dispose()


def test_training_plan_skips_session_that_overlaps_existing_training() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, employee, qualification = _add_trainable_gap(session, "BOOKED")
        booked_qualification = workforce_models.Qualification(
            code="QLF-BOOKED-OTHER",
            name="Qualificação já agendada",
            category="técnica",
            active=True,
        )
        target_catalog = workforce_models.TrainingCatalog(
            code="TRN-BOOKED-TARGET",
            name="Curso necessário",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        session.add_all((booked_qualification, target_catalog))
        session.flush()
        booked_catalog = workforce_models.TrainingCatalog(
            code="TRN-BOOKED-EXISTING",
            name="Curso já reservado",
            qualification_id=booked_qualification.id,
            duration_minutes=480,
            cost_cents=30_000,
            active=True,
        )
        session.add(booked_catalog)
        session.flush()
        booked_session = workforce_models.TrainingSession(
            training_catalog_id=booked_catalog.id,
            starts_at=datetime(2026, 9, 10, 8, tzinfo=UTC),
            ends_at=datetime(2026, 9, 10, 18, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        conflicting_session = workforce_models.TrainingSession(
            training_catalog_id=target_catalog.id,
            starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
            ends_at=datetime(2026, 9, 10, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        compatible_session = workforce_models.TrainingSession(
            training_catalog_id=target_catalog.id,
            starts_at=datetime(2026, 9, 11, 9, tzinfo=UTC),
            ends_at=datetime(2026, 9, 11, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        session.add_all((booked_session, conflicting_session, compatible_session))
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
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert len(plan.actions) == 1
    assert plan.actions[0].training_session_id == compatible_session.id
    engine.dispose()


def test_training_plan_never_books_overlapping_new_sessions_for_employee() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, employee, first_qualification = _add_trainable_gap(session, "DOUBLE")
        second_qualification = workforce_models.Qualification(
            code="QLF-DOUBLE-2",
            name="Segunda qualificação",
            category="técnica",
            active=True,
        )
        session.add(second_qualification)
        session.flush()
        result = session.scalar(
            select(operation_models.EligibilityResult).where(
                operation_models.EligibilityResult.employee_id == employee.id
            )
        )
        assert result is not None
        result.gaps = [
            {"qualification_id": str(first_qualification.id)},
            {"qualification_id": str(second_qualification.id)},
        ]
        first_catalog = workforce_models.TrainingCatalog(
            code="TRN-DOUBLE-1",
            name="Primeiro curso",
            qualification_id=first_qualification.id,
            duration_minutes=480,
            cost_cents=40_000,
            active=True,
        )
        second_catalog = workforce_models.TrainingCatalog(
            code="TRN-DOUBLE-2",
            name="Segundo curso",
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
                    starts_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                    ends_at=datetime(2026, 9, 10, 17, tzinfo=UTC),
                    capacity=10,
                    base_location="Curitiba",
                    status="open",
                ),
                workforce_models.TrainingSession(
                    training_catalog_id=second_catalog.id,
                    starts_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
                    ends_at=datetime(2026, 9, 10, 18, tzinfo=UTC),
                    capacity=10,
                    base_location="Curitiba",
                    status="open",
                ),
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).for_operation(operation.id)

    assert len(plan.actions) == 1
    assert len(plan.blockers) == 1
    engine.dispose()


def test_materializing_decision_training_records_the_source_session() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        operation, employee, qualification = _add_trainable_gap(session, "MAT")
        demand = session.scalar(
            select(operation_models.OperationRoleDemand).where(
                operation_models.OperationRoleDemand.operation_id == operation.id
            )
        )
        eligibility_run = session.scalar(
            select(operation_models.EligibilityRun).where(
                operation_models.EligibilityRun.operation_id == operation.id
            )
        )
        assert demand is not None and eligibility_run is not None
        decision = decision_models.DecisionRun(
            operation_id=operation.id,
            objective="MIN_COST",
            solver_version="9.15",
            rules_version="1.0.0",
            input_snapshot_hash="c" * 64,
            status="OPTIMAL",
            runtime_ms=10,
            metrics={"eligibility_run_id": str(eligibility_run.id)},
            candidate_snapshot=[],
            created_by="planner@example.com",
        )
        session.add(decision)
        session.flush()
        session.add(
            decision_models.DecisionAssignment(
                decision_run_id=decision.id,
                employee_id=employee.id,
                role_demand_id=demand.id,
                starts_at=operation.starts_at,
                ends_at=operation.ends_at,
                incremental_cost_cents=0,
            )
        )
        catalog = workforce_models.TrainingCatalog(
            code="TRN-MAT",
            name="Curso Materializado",
            qualification_id=qualification.id,
            duration_minutes=360,
            cost_cents=35_000,
            active=True,
        )
        session.add(catalog)
        session.flush()
        source_session = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2026, 9, 9, 9, tzinfo=UTC),
            ends_at=datetime(2026, 9, 9, 15, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        session.add(source_session)
        session.flush()
        source_session_id = source_session.id
        session.add(
            decision_models.DecisionTrainingAction(
                decision_run_id=decision.id,
                employee_id=employee.id,
                training_catalog_id=catalog.id,
                ready_at=datetime(2026, 9, 8, tzinfo=UTC),
                cost_cents=0,
                duration_minutes=0,
            )
        )
        session.add(
            operation_models.EligibilityRun(
                operation_id=operation.id,
                rules_version="1.0.0",
                input_hash="d" * 64,
                status="completed",
                started_at=datetime(2026, 8, 2, tzinfo=UTC),
                finished_at=datetime(2026, 8, 2, 0, 0, 1, tzinfo=UTC),
                candidate_count=0,
                evaluated_count=0,
            )
        )
        session.commit()

        plan = TrainingPlanningService(session).materialize_for_decision(decision.id)
        persisted = session.scalar(
            select(decision_models.DecisionTrainingAction).where(
                decision_models.DecisionTrainingAction.decision_run_id == decision.id
            )
        )

    assert persisted is not None
    assert persisted.training_session_id == source_session_id
    assert persisted.ready_at.replace(tzinfo=UTC) == datetime(2026, 9, 9, 15, tzinfo=UTC)
    assert persisted.cost_cents == 35_000
    assert persisted.duration_minutes == 360
    assert plan.actions[0].training_session_id == source_session_id
    engine.dispose()
