import re
import unicodedata
from dataclasses import dataclass

from app.imports.types import ImportContractName


@dataclass(frozen=True)
class ColumnDefinition:
    field: str
    aliases: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class ImportContract:
    name: ImportContractName
    version: str
    columns: tuple[ColumnDefinition, ...]


def normalize_header(value: str) -> str:
    ascii_value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().casefold())
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "_", ascii_value).strip("_")


CONTRACTS: dict[ImportContractName, ImportContract] = {
    "employees": ImportContract(
        name="employees",
        version="1.0",
        columns=(
            ColumnDefinition("employee_number", ("matricula", "id_colaborador", "employee_number")),
            ColumnDefinition("name", ("nome", "nome_completo", "name")),
            ColumnDefinition("email", ("email",), required=False),
            ColumnDefinition("role_code", ("codigo_cargo", "cargo", "funcao", "role_code")),
            ColumnDefinition("base_location", ("base", "localizacao", "base_location")),
            ColumnDefinition("seniority_level", ("senioridade", "nivel", "seniority_level")),
            ColumnDefinition("hired_on", ("data_admissao", "admissao", "hired_on")),
            ColumnDefinition("active", ("ativo", "status_ativo", "active"), required=False),
        ),
    ),
    "employee_qualifications": ImportContract(
        name="employee_qualifications",
        version="1.0",
        columns=(
            ColumnDefinition("employee_number", ("matricula", "employee_number")),
            ColumnDefinition(
                "qualification_code", ("codigo_qualificacao", "qualificacao", "qualification_code")
            ),
            ColumnDefinition("issued_on", ("emitida_em", "data_emissao", "issued_on")),
            ColumnDefinition(
                "expires_on", ("vence_em", "data_validade", "expires_on"), required=False
            ),
            ColumnDefinition("provider", ("provedor", "fornecedor", "provider"), required=False),
            ColumnDefinition(
                "external_identifier",
                ("identificador_externo", "certificado", "external_identifier"),
                required=False,
            ),
        ),
    ),
    "operations": ImportContract(
        name="operations",
        version="1.0",
        columns=(
            ColumnDefinition("code", ("codigo_operacao", "codigo", "code")),
            ColumnDefinition("name", ("operacao", "nome_operacao", "name")),
            ColumnDefinition("client_name", ("cliente", "client_name")),
            ColumnDefinition("base_location", ("base", "localizacao", "base_location")),
            ColumnDefinition("starts_at", ("inicio", "data_inicio", "starts_at")),
            ColumnDefinition("ends_at", ("fim", "data_fim", "ends_at")),
            ColumnDefinition(
                "mobilization_deadline", ("prazo_mobilizacao", "mobilization_deadline")
            ),
            ColumnDefinition("status", ("status",), required=False),
            ColumnDefinition(
                "budget_reais", ("orcamento_reais", "orcamento", "budget_reais"), required=False
            ),
            ColumnDefinition("role_code", ("codigo_cargo", "cargo", "role_code")),
            ColumnDefinition("quantity", ("quantidade", "vagas", "quantity")),
            ColumnDefinition("shift_code", ("turno", "shift_code"), required=False),
            ColumnDefinition("priority", ("prioridade", "priority"), required=False),
            ColumnDefinition(
                "qualification_code",
                ("qualificacao_obrigatoria", "qualification_code"),
                required=False,
            ),
            ColumnDefinition(
                "allows_training", ("permite_treinamento", "allows_training"), required=False
            ),
        ),
    ),
    "training_catalog": ImportContract(
        name="training_catalog",
        version="1.0",
        columns=(
            ColumnDefinition("code", ("codigo_treinamento", "codigo", "code")),
            ColumnDefinition("name", ("treinamento", "nome", "name")),
            ColumnDefinition("qualification_code", ("codigo_qualificacao", "qualification_code")),
            ColumnDefinition("duration_minutes", ("duracao_minutos", "duration_minutes")),
            ColumnDefinition("cost_reais", ("custo_reais", "custo", "cost_reais")),
            ColumnDefinition("active", ("ativo", "active"), required=False),
        ),
    ),
}


class ImportMappingError(ValueError):
    pass


def resolve_mapping(
    headers: list[str],
    contract: ImportContract,
    explicit: dict[str, str] | None = None,
) -> dict[str, str]:
    normalized_headers = {normalize_header(header): header for header in headers}
    if len(normalized_headers) != len(headers):
        raise ImportMappingError("duplicate_source_column")
    allowed_fields = {column.field for column in contract.columns}
    resolved: dict[str, str] = {}
    for raw_header, field in (explicit or {}).items():
        normalized = normalize_header(raw_header)
        if normalized not in normalized_headers or field not in allowed_fields:
            raise ImportMappingError("unknown_column_mapping")
        if field in resolved.values():
            raise ImportMappingError("duplicate_target_mapping")
        resolved[normalized_headers[normalized]] = field
    for column in contract.columns:
        if column.field in resolved.values():
            continue
        aliases = {normalize_header(alias) for alias in (column.field, *column.aliases)}
        matches = [
            original for normalized, original in normalized_headers.items() if normalized in aliases
        ]
        if len(matches) > 1:
            raise ImportMappingError("duplicate_target_mapping")
        if matches:
            resolved[matches[0]] = column.field
        elif column.required:
            raise ImportMappingError(f"missing_required_column:{column.field}")
    return resolved
