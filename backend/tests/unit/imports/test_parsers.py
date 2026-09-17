from io import BytesIO

import pytest
from openpyxl import Workbook

from app.imports.parsers import ImportFileError, parse_tabular_file


def test_csv_parser_preserves_unicode() -> None:
    headers, rows = parse_tabular_file(
        "colaboradores.csv",
        "Matrícula,Nome\nT-001,João da Conceição\n".encode(),
    )

    assert headers == ["Matrícula", "Nome"]
    assert rows == [{"Matrícula": "T-001", "Nome": "João da Conceição"}]


def test_xlsx_parser_rejects_formulas() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Matrícula", "Nome"])
    sheet.append(["T-001", '=CONCAT("Jo","ão")'])
    output = BytesIO()
    workbook.save(output)

    with pytest.raises(ImportFileError, match="formulas_not_allowed"):
        parse_tabular_file("colaboradores.xlsx", output.getvalue())


def test_parser_rejects_unsupported_files() -> None:
    with pytest.raises(ImportFileError, match="unsupported_file_format"):
        parse_tabular_file("colaboradores.xlsm", b"not-a-workbook")
