from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.decisions.models import AuditEvent
from app.operations import models as operation_models  # noqa: F401
from app.workforce.commands import (
    DuplicateEmployeeError,
    EmployeeCommandService,
    InvalidPeriodError,
    UnknownRoleError,
)
from app.workforce.models import Authorization, Qualification, Role, RoleFamily
from app.workforce.schemas import (
    EmployeeAuthorizationCreate,
    EmployeeAvailabilityCreate,
    EmployeeCostCreate,
    EmployeeCreate,
    EmployeeQualificationCreate,
)


def _session_with_role() -> tuple[Session, Role]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    family = RoleFamily(id=uuid4(), code="FAM-TEST", name="Família Teste", active=True)
    role = Role(
        family_id=family.id,
        code="ROLE-TEST",
        name="Cargo Teste",
        active=True,
    )
    session.add_all((family, role))
    session.commit()
    return session, role


def test_create_employee_rejects_duplicate_number() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session)
    command = EmployeeCreate(
        employee_number="EMP-001",
        name="Pessoa de Teste",
        canonical_role_id=role.id,
        base_location="Curitiba",
        seniority_level="pleno",
    )
    try:
        service.create_employee(command)
        session.flush()

        with pytest.raises(DuplicateEmployeeError):
            service.create_employee(command)
    finally:
        session.close()


def test_create_employee_rejects_unknown_role() -> None:
    session, _role = _session_with_role()
    service = EmployeeCommandService(session)
    try:
        with pytest.raises(UnknownRoleError):
            service.create_employee(
                EmployeeCreate(
                    employee_number="EMP-002",
                    name="Pessoa de Teste 2",
                    canonical_role_id=uuid4(),
                    base_location="Macaé",
                    seniority_level="sênior",
                )
            )
    finally:
        session.close()


def test_add_availability_rejects_overlapping_period() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session)
    employee = service.create_employee(
        EmployeeCreate(
            employee_number="EMP-003",
            name="Pessoa Disponibilidade",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
        )
    )
    first_period = EmployeeAvailabilityCreate(
        starts_at=datetime(2026, 10, 1, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, tzinfo=UTC),
        status="available",
    )
    overlapping_period = EmployeeAvailabilityCreate(
        starts_at=datetime(2026, 10, 15, tzinfo=UTC),
        ends_at=datetime(2026, 11, 15, tzinfo=UTC),
        status="available",
    )
    try:
        service.add_availability(employee.id, first_period)

        with pytest.raises(InvalidPeriodError, match="overlaps"):
            service.add_availability(employee.id, overlapping_period)
    finally:
        session.close()


def test_add_qualification_rejects_expiry_before_issue() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session)
    employee = service.create_employee(
        EmployeeCreate(
            employee_number="EMP-004",
            name="Pessoa Qualificação",
            canonical_role_id=role.id,
            base_location="Macaé",
            seniority_level="sênior",
        )
    )
    qualification = Qualification(
        code="QLF-DATE",
        name="Qualificação com validade",
        category="segurança",
        validity_days=365,
        active=True,
    )
    session.add(qualification)
    session.flush()
    try:
        with pytest.raises(InvalidPeriodError, match="expires_on"):
            service.add_qualification(
                employee.id,
                EmployeeQualificationCreate(
                    qualification_id=qualification.id,
                    issued_on=date(2026, 8, 10),
                    expires_on=date(2026, 8, 9),
                ),
            )
    finally:
        session.close()


def test_create_employee_records_actor_and_changed_fields_in_audit_event() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session, actor_id="planner@example.com")
    try:
        employee = service.create_employee(
            EmployeeCreate(
                employee_number="EMP-AUDIT-001",
                name="Pessoa Auditada",
                canonical_role_id=role.id,
                base_location="Curitiba",
                seniority_level="pleno",
            )
        )
        event = session.scalar(select(AuditEvent))
    finally:
        session.close()

    assert event is not None
    assert event.actor_id == "planner@example.com"
    assert event.event_type == "employee.created"
    assert event.aggregate_type == "employee"
    assert event.aggregate_id == employee.id
    assert event.payload["employee_number"] == "EMP-AUDIT-001"


def test_add_authorization_rejects_expiry_before_issue() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session)
    employee = service.create_employee(
        EmployeeCreate(
            employee_number="EMP-AUTH-DATE",
            name="Pessoa Autorização",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
        )
    )
    authorization = Authorization(
        code="AUT-DATE",
        name="Autorização com validade",
        scope_type="cliente",
        active=True,
    )
    session.add(authorization)
    session.flush()
    try:
        with pytest.raises(InvalidPeriodError, match="expires_on"):
            service.add_authorization(
                employee.id,
                EmployeeAuthorizationCreate(
                    authorization_id=authorization.id,
                    issued_on=date(2026, 8, 10),
                    expires_on=date(2026, 8, 9),
                ),
            )
    finally:
        session.close()


def test_add_cost_rejects_end_before_effective_start() -> None:
    session, role = _session_with_role()
    service = EmployeeCommandService(session)
    employee = service.create_employee(
        EmployeeCreate(
            employee_number="EMP-COST-DATE",
            name="Pessoa Custo",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
        )
    )
    try:
        with pytest.raises(InvalidPeriodError, match="effective_to"):
            service.add_cost(
                employee.id,
                EmployeeCostCreate(
                    hourly_cost_cents=12_000,
                    effective_from=date(2026, 8, 10),
                    effective_to=date(2026, 8, 9),
                ),
            )
    finally:
        session.close()
