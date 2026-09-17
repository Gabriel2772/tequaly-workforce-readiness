import pytest

from app.imports.contracts import CONTRACTS, ImportMappingError, resolve_mapping


def test_employee_contract_resolves_portuguese_aliases() -> None:
    mapping = resolve_mapping(
        ["Matrícula", "Nome completo", "Cargo", "Base", "Senioridade", "Data admissão"],
        CONTRACTS["employees"],
    )

    assert mapping["Matrícula"] == "employee_number"
    assert mapping["Nome completo"] == "name"
    assert mapping["Data admissão"] == "hired_on"


def test_contract_rejects_duplicate_target_and_missing_required_columns() -> None:
    with pytest.raises(ImportMappingError, match="duplicate_target_mapping"):
        resolve_mapping(
            ["Matrícula", "ID colaborador", "Nome", "Cargo", "Base", "Nível", "Admissão"],
            CONTRACTS["employees"],
        )

    with pytest.raises(ImportMappingError, match="missing_required_column:role_code"):
        resolve_mapping(
            ["Matrícula", "Nome", "Base", "Nível", "Admissão"],
            CONTRACTS["employees"],
        )
