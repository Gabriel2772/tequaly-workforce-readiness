from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ImportContractName = Literal[
    "employees",
    "employee_qualifications",
    "operations",
    "training_catalog",
]


class ImportPreviewCommand(BaseModel):
    contract: ImportContractName
    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    mapping: dict[str, str] = Field(default_factory=dict)


class ImportValidationError(BaseModel):
    row: int
    code: str
    field: str | None
    message: str


class ImportPreviewView(BaseModel):
    token: UUID
    contract: ImportContractName
    contract_version: str
    filename: str
    source_hash: str
    mapping: dict[str, str]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ImportValidationError]
    sample_rows: list[dict[str, object]]
    expires_at: str


class ImportCommitCommand(BaseModel):
    preview_token: UUID
    confirmed: bool


class ImportCommitSummary(BaseModel):
    batch_id: UUID
    contract: ImportContractName
    created: int
    updated: int
    total: int
    idempotent: bool = False
