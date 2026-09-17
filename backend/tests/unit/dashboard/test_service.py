from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import models as auth_models  # noqa: F401
from app.dashboard.service import DashboardService
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.operations import models as operation_models
from app.workforce import models as workforce_models


def test_dashboard_aggregates_readiness_risk_expiry_and_training_cost() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime(2030, 1, 1, 8, tzinfo=UTC)

    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="DASH-FAM", name="Dashboard")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="DASH-ROLE",
            name="Montador Dashboard",
            active=True,
        )
        qualification = workforce_models.Qualification(
            code="DASH-QLF",
            name="NR Dashboard",
            category="seguranca",
            active=True,
        )
        session.add_all((role, qualification))
        session.flush()
        active_employee = workforce_models.Employee(
            employee_number="DASH-001",
            name="Pessoa Ativa",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        inactive_employee = workforce_models.Employee(
            employee_number="DASH-002",
            name="Pessoa Inativa",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=False,
        )
        operation = operation_models.Operation(
            code="DASH-OPS",
            name="Parada Dashboard",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2030, 1, 20, tzinfo=UTC),
            ends_at=datetime(2030, 1, 31, tzinfo=UTC),
            mobilization_deadline=datetime(2030, 1, 10, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add_all((active_employee, inactive_employee, operation))
        session.flush()
        session.add(
            workforce_models.EmployeeQualification(
                employee_id=active_employee.id,
                qualification_id=qualification.id,
                issued_on=date(2029, 1, 15),
                expires_on=date(2030, 1, 15),
                workload_minutes=480,
                provider="Provider",
            )
        )
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
            input_hash="7" * 64,
            status="completed",
            started_at=now,
            finished_at=datetime(2030, 1, 1, 8, 0, 1, tzinfo=UTC),
            candidate_count=1,
            evaluated_count=1,
            eligible_count=1,
        )
        session.add_all((demand, run))
        session.flush()
        session.add(
            operation_models.EligibilityResult(
                eligibility_run_id=run.id,
                employee_id=active_employee.id,
                role_demand_id=demand.id,
                classification="ELIGIBLE",
                reason_codes=[],
                reasons=[],
                gaps=[],
                required_training_ids=[],
                incremental_cost_cents=0,
            )
        )
        catalog = workforce_models.TrainingCatalog(
            code="DASH-TRN",
            name="Curso Dashboard",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=30_000,
            active=True,
        )
        session.add(catalog)
        session.flush()
        training_session = workforce_models.TrainingSession(
            training_catalog_id=catalog.id,
            starts_at=datetime(2030, 1, 5, 9, tzinfo=UTC),
            ends_at=datetime(2030, 1, 5, 17, tzinfo=UTC),
            capacity=10,
            base_location="Curitiba",
            status="open",
        )
        session.add(training_session)
        session.flush()
        session.add(
            workforce_models.EmployeeTrainingPlan(
                employee_id=active_employee.id,
                training_session_id=training_session.id,
                operation_id=operation.id,
                status="planned",
                due_at=training_session.ends_at,
            )
        )
        session.commit()

        overview = DashboardService(session, clock=lambda: now).get_overview(30)

    assert overview.active_employee_count == 1
    assert overview.readiness_percent == 50.0
    assert overview.expiring_qualification_count == 1
    assert overview.risky_operation_count == 1
    assert overview.uncovered_position_count == 1
    assert overview.planned_training_cost_cents == 30_000
    assert overview.upcoming_operations[0].name == "Parada Dashboard"
    assert overview.upcoming_operations[0].severity == "critical"
    assert overview.risk_alerts[0].role_name == "Montador Dashboard"
    assert overview.expiring_qualifications[0].employee_name == "Pessoa Ativa"
    engine.dispose()


def test_dashboard_does_not_label_unassessed_operation_as_critical() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime(2030, 1, 1, 8, tzinfo=UTC)

    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="PEND-FAM", name="Pendente")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="PEND-ROLE",
            name="Cargo pendente",
            active=True,
        )
        operation = operation_models.Operation(
            code="PEND-OPS",
            name="Operacao sem avaliacao",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2030, 1, 20, tzinfo=UTC),
            ends_at=datetime(2030, 1, 31, tzinfo=UTC),
            mobilization_deadline=datetime(2030, 1, 10, tzinfo=UTC),
            status="planning",
            budget_cents=None,
        )
        session.add_all((role, operation))
        session.flush()
        session.add(
            operation_models.OperationRoleDemand(
                operation_id=operation.id,
                role_id=role.id,
                quantity=5,
                shift_code="day",
                priority=10,
            )
        )
        session.commit()

        overview = DashboardService(session, clock=lambda: now).get_overview(30)

    assert overview.readiness_percent is None
    assert overview.risky_operation_count == 0
    assert overview.uncovered_position_count == 0
    assert overview.risk_alerts == []
    assert overview.upcoming_operations[0].analysis_status == "pending"
    assert overview.upcoming_operations[0].severity == "unknown"
    engine.dispose()
