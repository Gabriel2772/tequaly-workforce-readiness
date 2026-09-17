from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.imports.contracts import CONTRACTS, resolve_mapping
from app.imports.parsers import parse_tabular_file
from app.imports.validators import ImportRowValidator, map_source_rows

SAMPLE_ROOT = Path(__file__).parents[4] / "samples"


def test_all_valid_samples_round_trip_through_canonical_contracts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    samples = {
        "employees": "employees.csv",
        "employee_qualifications": "employee_qualifications.csv",
        "operations": "operations.xlsx",
        "training_catalog": "training_catalog.xlsx",
    }
    with Session(engine) as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()
        validator = ImportRowValidator(session)
        for contract_name, filename in samples.items():
            headers, rows = parse_tabular_file(filename, (SAMPLE_ROOT / filename).read_bytes())
            contract = CONTRACTS[contract_name]  # type: ignore[index]
            mapping = resolve_mapping(headers, contract)
            normalized, errors = validator.validate(contract, map_source_rows(rows, mapping))

            assert errors == [], filename
            assert len(normalized) == 2, filename
    engine.dispose()


def test_invalid_sample_remains_invalid_for_demonstration() -> None:
    headers, rows = parse_tabular_file(
        "employees-invalid.csv", (SAMPLE_ROOT / "employees-invalid.csv").read_bytes()
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()
        contract = CONTRACTS["employees"]
        normalized, errors = ImportRowValidator(session).validate(
            contract, map_source_rows(rows, resolve_mapping(headers, contract))
        )

    assert normalized == []
    assert errors[0].code == "unknown_role"
    engine.dispose()
