from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.operations.schemas import OperationCreate


def test_operation_end_must_follow_start() -> None:
    starts_at = datetime(2026, 10, 2, tzinfo=UTC)
    ends_at = datetime(2026, 10, 1, tzinfo=UTC)

    with pytest.raises(ValidationError, match="ends_at"):
        OperationCreate(
            code="OPS-DATE",
            name="Operação inválida",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=starts_at,
            ends_at=ends_at,
            status="planning",
            demands=[],
            requirements=[],
        )
