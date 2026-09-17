from datetime import timedelta

from app.demo.generator import REFERENCE_DATE, generate_demo_dataset
from app.demo.seed import stable_demo_id


def test_demo_generator_is_deterministic() -> None:
    assert generate_demo_dataset(42, 20) == generate_demo_dataset(42, 20)


def test_stable_ids_include_seed_and_natural_key() -> None:
    assert stable_demo_id(42, "employee", "SYN-00001") == stable_demo_id(
        42, "employee", "SYN-00001"
    )
    assert stable_demo_id(42, "employee", "SYN-00001") != stable_demo_id(
        43, "employee", "SYN-00001"
    )


def test_main_dataset_shape() -> None:
    data = generate_demo_dataset(42, 2_200)

    assert len(data.employees) == 2_200
    assert len(data.role_families) == 12
    assert len(data.canonical_roles) == 90
    assert len(data.role_aliases) == 130
    assert len(data.bases) == 5
    assert len(data.qualifications) + len(data.authorizations) + len(data.training_catalog) == 120
    assert len(data.operations) == 8
    assert all(
        operation.mobilization_deadline < operation.starts_at for operation in data.operations
    )
    assert len(data.employee_availability) == 6_600
    assert {window.status for window in data.employee_availability} == {
        "available",
        "unavailable",
    }


def test_employee_records_are_explicitly_synthetic() -> None:
    data = generate_demo_dataset(7, 5)

    assert all(employee.name.startswith("Colaborador Sintético ") for employee in data.employees)
    assert all(employee.employee_number.startswith("SYN-") for employee in data.employees)


def test_dataset_contains_controlled_expiry_and_infeasibility_cases() -> None:
    data = generate_demo_dataset(42, 2_200)
    expiring_limit = REFERENCE_DATE + timedelta(days=30)
    dated_links = [link for link in data.employee_qualifications if link.expires_on]
    expired = [link for link in dated_links if link.expires_on < REFERENCE_DATE]
    expiring = [link for link in dated_links if REFERENCE_DATE <= link.expires_on <= expiring_limit]

    assert expired
    assert len(expired) / len(dated_links) < 0.08
    assert expiring
    assert max(demand.quantity for demand in data.role_demands) == 75
    assert any(operation.status == "infeasible_demo" for operation in data.operations)


def test_dataset_encodes_conflicts_trainable_gaps_and_cost_tradeoffs() -> None:
    data = generate_demo_dataset(42, 2_200)

    assert len(data.employee_costs) == 2_200
    assert len({cost.hourly_cost_cents for cost in data.employee_costs}) > 10
    assert data.employee_assignments
    assert len(data.training_sessions) == 24
    assert len(data.requirements) == len(data.role_demands)
    assert all(requirement.allows_training for requirement in data.requirements)
