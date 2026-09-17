from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.decisions.schemas import RecordOutcomeCommand


@pytest.mark.parametrize(
    ("observation", "invalid_field"),
    [
        (
            {
                "parameter": "unsupported_parameter",
                "category": "seguranca",
                "value": "100",
            },
            "parameter",
        ),
        (
            {
                "parameter": "training_cost_cents",
                "category": "seguranca",
                "value": "-1",
            },
            "value",
        ),
    ],
)
def test_outcome_rejects_invalid_calibration_observation(
    observation: dict[str, str], invalid_field: str
) -> None:
    with pytest.raises(ValidationError) as error:
        RecordOutcomeCommand(
            actual_cost_cents=100,
            actual_ready_at=datetime(2030, 1, 1, tzinfo=UTC),
            calibration_observations=[observation],
        )

    assert invalid_field in str(error.value)
