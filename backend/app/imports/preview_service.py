import base64
from binascii import Error as Base64Error
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from sqlalchemy.orm import Session

from app.imports.contracts import CONTRACTS, ImportMappingError, resolve_mapping
from app.imports.models import ImportBatch
from app.imports.parsers import ImportFileError, parse_tabular_file
from app.imports.types import ImportPreviewCommand, ImportPreviewView
from app.imports.validators import ImportRowValidator, map_source_rows


class ImportPreviewError(ValueError):
    pass


class ImportPreviewService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def preview(self, command: ImportPreviewCommand) -> ImportPreviewView:
        try:
            content = base64.b64decode(command.content_base64, validate=True)
            headers, source_rows = parse_tabular_file(command.filename, content)
            contract = CONTRACTS[command.contract]
            mapping = resolve_mapping(headers, contract, command.mapping)
        except (Base64Error, ImportFileError, ImportMappingError) as error:
            raise ImportPreviewError(str(error) or "invalid_import") from error
        mapped_rows = map_source_rows(source_rows, mapping)
        normalized_rows, errors = ImportRowValidator(self._session).validate(contract, mapped_rows)
        invalid_row_numbers = {error.row for error in errors}
        expires_at = datetime.now(UTC) + timedelta(minutes=30)
        batch = ImportBatch(
            contract_name=contract.name,
            contract_version=contract.version,
            filename=command.filename,
            source_hash=sha256(content).hexdigest(),
            mapping=mapping,
            normalized_rows=normalized_rows,
            validation_errors=[error.model_dump(mode="json") for error in errors],
            total_rows=len(source_rows),
            valid_rows=len(source_rows) - len(invalid_row_numbers),
            invalid_rows=len(invalid_row_numbers),
            status="previewed",
            actor_id=self._actor_id,
            expires_at=expires_at,
        )
        self._session.add(batch)
        self._session.flush()
        return ImportPreviewView(
            token=batch.id,
            contract=contract.name,
            contract_version=contract.version,
            filename=command.filename,
            source_hash=batch.source_hash,
            mapping=mapping,
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            invalid_rows=batch.invalid_rows,
            errors=errors,
            sample_rows=normalized_rows[:5],
            expires_at=expires_at.isoformat(),
        )
