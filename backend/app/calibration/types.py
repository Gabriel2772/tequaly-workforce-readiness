from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RobustEstimate(BaseModel):
    value: Decimal
    sample_size: int
    minimum_sample_size: int
    confidence_basis: str
    interquartile_range: Decimal


CalibrationParameterName = Literal[
    "training_cost_cents",
    "mobilization_lead_time_days",
    "travel_cost_cents",
]


class CalibrationObservation(BaseModel):
    parameter: CalibrationParameterName
    category: str = Field(min_length=1, max_length=160)
    value: Decimal = Field(ge=0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("category must not be blank")
        return normalized


class CreateCalibrationSuggestionCommand(BaseModel):
    parameter: CalibrationParameterName
    category: str = Field(min_length=1, max_length=160)


class ApplyCalibrationSuggestionCommand(BaseModel):
    confirmed: bool


class CalibrationSuggestionView(BaseModel):
    id: UUID
    parameter_name: str
    category: str
    current_value: Decimal
    proposed_value: Decimal
    sample_size: int
    confidence_basis: str
    interquartile_range: Decimal
    rationale: str
    status: str
    created_by: str
    created_at: datetime
    applied_by: str | None
    applied_at: datetime | None


class CalibrationParameterView(BaseModel):
    id: UUID
    name: str
    version: str
    value: Decimal
    rationale: str | None
    created_at: datetime
