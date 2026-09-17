from app.exports.service import safe_spreadsheet_value, validate_export_type


def test_spreadsheet_formula_prefixes_are_escaped() -> None:
    assert safe_spreadsheet_value('=HYPERLINK("bad")') == '\'=HYPERLINK("bad")'
    assert safe_spreadsheet_value("+1+1") == "'+1+1"
    assert safe_spreadsheet_value("Pessoa segura") == "Pessoa segura"


def test_export_type_is_allowlisted() -> None:
    assert validate_export_type("employees") == "employees"
