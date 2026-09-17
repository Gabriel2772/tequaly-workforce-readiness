from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.imports.contracts import ImportContract, normalize_header
from app.imports.types import ImportValidationError
from app.workforce.models import Employee, Qualification, Role, RoleAlias, TrainingCatalog


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _date_value(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError("invalid_date")


def _datetime_value(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
    else:
        text = _text(value)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = datetime.combine(_date_value(text), time.min)
            except ValueError as error:
                raise ValueError("invalid_datetime") from error
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _boolean(value: object, default: bool) -> bool:
    text = _text(value).casefold()
    if not text:
        return default
    if text in {"1", "true", "sim", "yes", "ativo"}:
        return True
    if text in {"0", "false", "nao", "não", "no", "inativo"}:
        return False
    raise ValueError("invalid_boolean")


def _positive_integer(value: object, default: int | None = None) -> int:
    if _text(value) == "" and default is not None:
        return default
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("invalid_integer") from error
    if parsed <= 0:
        raise ValueError("must_be_positive")
    return parsed


def _money_cents(value: object, default: int | None = None) -> int:
    if _text(value) == "" and default is not None:
        return default
    normalized = _text(value).replace("R$", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError("invalid_money") from error
    if amount < 0:
        raise ValueError("must_be_non_negative")
    return int((amount * 100).quantize(Decimal("1")))


class ImportRowValidator:
    def __init__(self, session: Session) -> None:
        self._role_codes = {
            role.code.casefold(): role.code for role in session.scalars(select(Role))
        }
        self._role_aliases: dict[str, str] = {}
        role_code_by_id = {role.id: role.code for role in session.scalars(select(Role))}
        for alias in session.scalars(select(RoleAlias).where(RoleAlias.active.is_(True))):
            role_code = role_code_by_id.get(alias.role_id)
            if role_code:
                self._role_aliases[normalize_header(alias.source_title)] = role_code
                self._role_aliases[normalize_header(alias.normalized_title)] = role_code
        self._qualification_codes = {
            qualification.code.casefold(): qualification.code
            for qualification in session.scalars(select(Qualification))
        }
        self._existing_employees = set(session.scalars(select(Employee.employee_number)))
        self._existing_training = set(session.scalars(select(TrainingCatalog.code)))

    def validate(
        self,
        contract: ImportContract,
        mapped_rows: list[dict[str, object]],
    ) -> tuple[list[dict[str, object]], list[ImportValidationError]]:
        normalized: list[dict[str, object]] = []
        errors: list[ImportValidationError] = []
        seen: set[tuple[object, ...]] = set()
        operation_facts: dict[str, tuple[object, ...]] = {}
        for index, row in enumerate(mapped_rows, start=2):
            missing = [
                column.field
                for column in contract.columns
                if column.required and not _text(row.get(column.field))
            ]
            if missing:
                errors.extend(
                    ImportValidationError(
                        row=index,
                        code="missing_required_field",
                        field=field,
                        message=f"O campo obrigatório {field} está vazio.",
                    )
                    for field in missing
                )
                continue
            try:
                item = self._normalize(contract.name, row)
            except ValueError as error:
                code, _, field = str(error).partition(":")
                errors.append(
                    ImportValidationError(
                        row=index,
                        code=code,
                        field=field or None,
                        message=f"Valor inválido em {field or 'linha'} ({code}).",
                    )
                )
                continue
            key = self._natural_key(contract.name, item)
            if key in seen:
                errors.append(
                    ImportValidationError(
                        row=index,
                        code="duplicate_natural_key",
                        field=None,
                        message="A linha repete uma chave natural já presente no arquivo.",
                    )
                )
                continue
            seen.add(key)
            if contract.name == "operations":
                code = str(item["code"])
                facts = tuple(
                    item[field]
                    for field in (
                        "name",
                        "client_name",
                        "base_location",
                        "starts_at",
                        "ends_at",
                        "mobilization_deadline",
                        "status",
                        "budget_cents",
                    )
                )
                if code in operation_facts and operation_facts[code] != facts:
                    errors.append(
                        ImportValidationError(
                            row=index,
                            code="inconsistent_operation",
                            field="code",
                            message=(
                                "Linhas da mesma operação possuem dados de "
                                "cabeçalho divergentes."
                            ),
                        )
                    )
                    continue
                operation_facts[code] = facts
            item["_action"] = self._action(contract.name, item)
            normalized.append(item)
        return normalized, errors

    def _role_code(self, value: object) -> str:
        text = _text(value)
        code = self._role_codes.get(text.casefold()) or self._role_aliases.get(
            normalize_header(text)
        )
        if code is None:
            raise ValueError("unknown_role:role_code")
        return code

    def _qualification_code(self, value: object) -> str:
        code = self._qualification_codes.get(_text(value).casefold())
        if code is None:
            raise ValueError("unknown_qualification:qualification_code")
        return code

    def _normalize(self, name: str, row: dict[str, object]) -> dict[str, object]:
        if name == "employees":
            return {
                "employee_number": _text(row["employee_number"]),
                "name": _text(row["name"]),
                "email": _text(row.get("email")) or None,
                "role_code": self._role_code(row["role_code"]),
                "base_location": _text(row["base_location"]),
                "seniority_level": _text(row["seniority_level"]),
                "hired_on": _date_value(row["hired_on"]).isoformat(),
                "active": _boolean(row.get("active"), True),
            }
        if name == "employee_qualifications":
            employee_number = _text(row["employee_number"])
            if employee_number not in self._existing_employees:
                raise ValueError("unknown_employee:employee_number")
            issued_on = _date_value(row["issued_on"])
            expires_on = _date_value(row["expires_on"]) if _text(row.get("expires_on")) else None
            if expires_on is not None and expires_on < issued_on:
                raise ValueError("invalid_period:expires_on")
            return {
                "employee_number": employee_number,
                "qualification_code": self._qualification_code(row["qualification_code"]),
                "issued_on": issued_on.isoformat(),
                "expires_on": expires_on.isoformat() if expires_on else None,
                "provider": _text(row.get("provider")) or None,
                "external_identifier": _text(row.get("external_identifier")) or None,
            }
        if name == "operations":
            starts_at = _datetime_value(row["starts_at"])
            ends_at = _datetime_value(row["ends_at"])
            deadline = _datetime_value(row["mobilization_deadline"])
            if ends_at <= starts_at or deadline > starts_at:
                raise ValueError("invalid_period:ends_at")
            qualification = _text(row.get("qualification_code"))
            return {
                "code": _text(row["code"]),
                "name": _text(row["name"]),
                "client_name": _text(row["client_name"]),
                "base_location": _text(row["base_location"]),
                "starts_at": starts_at.isoformat(),
                "ends_at": ends_at.isoformat(),
                "mobilization_deadline": deadline.isoformat(),
                "status": _text(row.get("status")) or "planning",
                "budget_cents": _money_cents(row.get("budget_reais"), 0),
                "role_code": self._role_code(row["role_code"]),
                "quantity": _positive_integer(row["quantity"]),
                "shift_code": _text(row.get("shift_code")) or "default",
                "priority": _positive_integer(row.get("priority"), 100),
                "qualification_code": (
                    self._qualification_code(qualification) if qualification else None
                ),
                "allows_training": _boolean(row.get("allows_training"), True),
            }
        if name == "training_catalog":
            return {
                "code": _text(row["code"]),
                "name": _text(row["name"]),
                "qualification_code": self._qualification_code(row["qualification_code"]),
                "duration_minutes": _positive_integer(row["duration_minutes"]),
                "cost_cents": _money_cents(row["cost_reais"]),
                "active": _boolean(row.get("active"), True),
            }
        raise ValueError("unknown_contract")

    @staticmethod
    def _natural_key(name: str, item: dict[str, object]) -> tuple[object, ...]:
        if name == "employees":
            return (item["employee_number"],)
        if name == "employee_qualifications":
            return (item["employee_number"], item["qualification_code"], item["issued_on"])
        if name == "operations":
            return (item["code"], item["role_code"], item["shift_code"])
        return (item["code"],)

    def _action(self, name: str, item: dict[str, object]) -> str:
        if name == "employees":
            return "update" if item["employee_number"] in self._existing_employees else "create"
        if name == "training_catalog":
            return "update" if item["code"] in self._existing_training else "create"
        return "upsert"


def map_source_rows(
    source_rows: list[dict[str, object]], mapping: dict[str, str]
) -> list[dict[str, Any]]:
    return [{target: row.get(source) for source, target in mapping.items()} for row in source_rows]
