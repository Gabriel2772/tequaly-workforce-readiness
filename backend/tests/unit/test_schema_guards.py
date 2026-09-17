from sqlalchemy import MetaData

from app.db.base import Base

SPEC_MINIMUM_TABLES = {
    "app_users",
    "audit_events",
    "authorizations",
    "calibration_parameters",
    "decision_assignments",
    "decision_outcomes",
    "decision_runs",
    "decision_training_actions",
    "eligibility_results",
    "eligibility_runs",
    "employee_assignments",
    "employee_authorizations",
    "employee_availability",
    "employee_cost_profiles",
    "employee_qualifications",
    "employee_role_history",
    "employee_training_plans",
    "employees",
    "operation_requirements",
    "operation_role_demands",
    "operations",
    "qualifications",
    "requirement_qualification_map",
    "roles",
    "training_catalog",
    "training_sessions",
}


def _metadata() -> MetaData:
    # Import modules explicitly so every mapping is registered on Base.metadata.
    from app.auth import models as auth_models  # noqa: F401
    from app.decisions import models as decision_models  # noqa: F401
    from app.imports import models as import_models  # noqa: F401
    from app.operations import models as operation_models  # noqa: F401
    from app.workforce import models as workforce_models  # noqa: F401

    return Base.metadata


def test_required_tables_exist() -> None:
    assert set(_metadata().tables) >= SPEC_MINIMUM_TABLES


def test_schema_has_no_document_evidence_table() -> None:
    table_names = {name.casefold() for name in _metadata().tables}

    assert "evidence" not in table_names
    assert "evidences" not in table_names


def test_all_tables_use_uuid_primary_keys() -> None:
    for table in _metadata().tables.values():
        primary_key_columns = list(table.primary_key.columns)
        assert len(primary_key_columns) == 1, table.name
        assert primary_key_columns[0].type.python_type.__name__ == "UUID", table.name
