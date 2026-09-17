from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class OperationRoleDemandCreate(BaseModel):
    role_id: UUID
    quantity: int = Field(ge=1)
    shift_code: str = Field(default="default", min_length=1, max_length=32)
    priority: int = Field(default=100, ge=1)
    compatible_role_ids: list[UUID] = Field(default_factory=list)


class OperationRequirementCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=180)
    requirement_type: str = Field(min_length=1, max_length=48)
    mandatory: bool = True
    role_id: UUID | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    qualification_ids: list[UUID] = Field(default_factory=list)
    minimum_level: str | None = Field(default=None, max_length=48)
    allows_training: bool = False


class OperationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=180)
    client_name: str = Field(min_length=1, max_length=180)
    base_location: str = Field(min_length=1, max_length=80)
    starts_at: datetime
    ends_at: datetime
    mobilization_deadline: datetime | None = None
    status: str = Field(default="planning", min_length=1, max_length=32)
    budget_cents: int | None = Field(default=None, ge=0)
    demands: list[OperationRoleDemandCreate] = Field(default_factory=list)
    requirements: list[OperationRequirementCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self) -> "OperationCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        if self.mobilization_deadline is not None and self.mobilization_deadline > self.starts_at:
            raise ValueError("mobilization_deadline must not be later than starts_at")
        return self


class OperationWriteResult(BaseModel):
    id: UUID
    code: str
    updated_at: datetime


class OperationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    client_name: str | None = Field(default=None, min_length=1, max_length=180)
    base_location: str | None = Field(default=None, min_length=1, max_length=80)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    mobilization_deadline: datetime | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    budget_cents: int | None = Field(default=None, ge=0)


class OperationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    client_name: str
    base_location: str
    starts_at: datetime
    ends_at: datetime
    mobilization_deadline: datetime | None
    status: str
    budget_cents: int | None
    updated_at: datetime

    @field_serializer("starts_at", "ends_at", "mobilization_deadline")
    def serialize_utc_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class PaginatedOperations(BaseModel):
    items: list[OperationView]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class OperationRoleDemandView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_id: UUID
    quantity: int
    shift_code: str
    priority: int


class OperationRoleDemandUpdate(BaseModel):
    role_id: UUID | None = None
    quantity: int | None = Field(default=None, ge=1)
    shift_code: str | None = Field(default=None, min_length=1, max_length=32)
    priority: int | None = Field(default=None, ge=1)


class OperationRequirementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    requirement_type: str | None = Field(default=None, min_length=1, max_length=48)
    mandatory: bool | None = None
    payload: dict[str, object] | None = None


class OperationDetail(OperationView):
    demands: list[OperationRoleDemandView]
    requirements: list["OperationRequirementView"]


class OperationRequirementView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_demand_id: UUID | None
    code: str
    name: str
    requirement_type: str
    mandatory: bool
    payload: dict[str, object]
