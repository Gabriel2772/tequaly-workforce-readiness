from io import BytesIO

import pytest
from openpyxl import Workbook

from app.imports.parsers import ImportFileError, parse_tabular_file


def test_csv_parser_preserves_unicode() -> None:
    headers, rows = parse_tabular_file(
        "colaboradores.csv",
        "Matr�cula,Nome\nT-001,Jo�o da Concei��o\n".encode(),
    )

    assert headers == ["Matr�cula", "Nome"]
    assert rows == [{"Matr�cula": "T-001", "Nome": "Jo�o da Concei��o"}]


def test_xlsx_parser_rejects_formulas() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Matr�cula", "Nome"])
    sheet.append(["T-001", '=CONCAT("Jo","�o")'])
    output = BytesIO()
    workbook.save(output)

    with pytest.raises(ImportFileError, match="formulas_not_allowed"):
        parse_tabular_file("colaboradores.xlsx", output.getvalue())


def test_parser_rejects_unsupported_files() -> None:
    with pytest.raises(ImportFileError, match="unsupported_file_format"):
        parse_tabular_file("colaboradores.xlsm", b"not-a-workbook")
