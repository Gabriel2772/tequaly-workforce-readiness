from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualificationSummary(BaseModel):
    id: UUID
    nome: str
    categoria: str
    emitida_em: date
    vence_em: date | None
    status: str


class TechnicalCompetencySummary(BaseModel):
    nome: str
    nivel: int
    avaliada_em: date


class AuthorizationSummary(BaseModel):
    nome: str
    escopo: str | None
    vence_em: date | None
    status: str


class AvailabilitySummary(BaseModel):
    inicio: datetime
    fim: datetime
    status: str


class AssignmentSummary(BaseModel):
    operacao: str
    inicio: datetime
    fim: datetime
    status: str


class CostSummary(BaseModel):
    moeda: str
    custo_hora_centavos: int
    custo_viagem_centavos: int
    vigencia_inicio: date


class TrainingSummary(BaseModel):
    treinamento: str
    inicio: datetime
    fim: datetime
    status: str


class RestrictionSummary(BaseModel):
    restricao: str
    escopo: str | None
    inicio: datetime | None
    fim: datetime | None


class EmployeeProfileVector(BaseModel):
    cargo_funcao_principal: str
    nome: str
    qualificacoes: list[QualificationSummary]
    competencias_tecnicas: list[TechnicalCompetencySummary]
    autorizacoes: list[AuthorizationSummary]
    disponibilidade: list[AvailabilitySummary]
    base_localizacao: str
    experiencia_senioridade: str
    alocacoes: list[AssignmentSummary]
    custos_incrementais: list[CostSummary]
    capacitacoes_agendadas: list[TrainingSummary]
    restricoes_operacionais: list[RestrictionSummary]
    prontidao: dict[str, object]
    updated_at: datetime


class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_number: str
    name: str
    role_name: str
    base_location: str
    seniority_level: str
    active: bool
    updated_at: datetime


class PaginatedEmployees(BaseModel):
    items: list[EmployeeListItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class EmployeeCreate(BaseModel):
    employee_number: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=180)
    email: str | None = Field(default=None, max_length=254)
    canonical_role_id: UUID
    base_location: str = Field(min_length=1, max_length=80)
    seniority_level: str = Field(min_length=1, max_length=40)
    hired_on: date | None = None
    active: bool = True


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    email: str | None = Field(default=None, max_length=254)
    canonical_role_id: UUID | None = None
    base_location: str | None = Field(default=None, min_length=1, max_length=80)
    seniority_level: str | None = Field(default=None, min_length=1, max_length=40)
    hired_on: date | None = None
    active: bool | None = None


class EmployeeWriteResult(BaseModel):
    id: UUID
    employee_number: str
    updated_at: datetime


class QualificationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=180)
    category: str = Field(min_length=1, max_length=64)
    method: str | None = Field(default=None, max_length=80)
    level: str | None = Field(default=None, max_length=48)
    validity_days: int | None = Field(default=None, ge=1)
    active: bool = True


class QualificationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    method: str | None = Field(default=None, max_length=80)
    level: str | None = Field(default=None, max_length=48)
    validity_days: int | None = Field(default=None, ge=1)
    active: bool | None = None


class QualificationReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: str
    method: str | None
    level: str | None
    validity_days: int | None
    active: bool
    updated_at: datetime


class PaginatedQualifications(BaseModel):
    items: list[QualificationReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class RoleCreate(BaseModel):
    family_id: UUID
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=160)
    active: bool = True


class RoleUpdate(BaseModel):
    family_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    active: bool | None = None


class RoleReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    code: str
    name: str
    active: bool
    updated_at: datetime


class PaginatedRoles(BaseModel):
    items: list[RoleReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class RoleAliasCreate(BaseModel):
    role_id: UUID
    source_title: str = Field(min_length=1, max_length=200)
    normalized_title: str = Field(min_length=1, max_length=200)
    active: bool = True


class RoleAliasUpdate(BaseModel):
    role_id: UUID | None = None
    source_title: str | None = Field(default=None, min_length=1, max_length=200)
    normalized_title: str | None = Field(default=None, min_length=1, max_length=200)
    active: bool | None = None


class RoleAliasReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_id: UUID
    source_title: str
    normalized_title: str
    active: bool
    updated_at: datetime


class PaginatedRoleAliases(BaseModel):
    items: list[RoleAliasReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class AuthorizationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=180)
    scope_type: str = Field(min_length=1, max_length=48)
    active: bool = True


class AuthorizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    scope_type: str | None = Field(default=None, min_length=1, max_length=48)
    active: bool | None = None


class AuthorizationReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    scope_type: str
    active: bool
    updated_at: datetime


class PaginatedAuthorizations(BaseModel):
    items: list[AuthorizationReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class TrainingCatalogCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=180)
    qualification_id: UUID
    duration_minutes: int = Field(ge=1)
    cost_cents: int = Field(default=0, ge=0)
    active: bool = True


class TrainingCatalogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    qualification_id: UUID | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    cost_cents: int | None = Field(default=None, ge=0)
    active: bool | None = None


class TrainingCatalogReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    qualification_id: UUID
    duration_minutes: int
    cost_cents: int
    active: bool
    updated_at: datetime


class PaginatedTrainingCatalog(BaseModel):
    items: list[TrainingCatalogReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class TechnicalCompetencyCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=160)
    scale_max: int = Field(default=5, ge=1)
    active: bool = True


class TechnicalCompetencyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    scale_max: int | None = Field(default=None, ge=1)
    active: bool | None = None


class TechnicalCompetencyReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    scale_max: int
    active: bool
    updated_at: datetime


class PaginatedTechnicalCompetencies(BaseModel):
    items: list[TechnicalCompetencyReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class OperationalRestrictionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=180)
    hard_constraint: bool = True
    active: bool = True


class OperationalRestrictionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    hard_constraint: bool | None = None
    active: bool | None = None


class OperationalRestrictionReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    hard_constraint: bool
    active: bool
    updated_at: datetime


class PaginatedOperationalRestrictions(BaseModel):
    items: list[OperationalRestrictionReference]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class CreatedRecord(BaseModel):
    id: UUID


class EmployeeQualificationCreate(BaseModel):
    qualification_id: UUID
    issued_on: date
    expires_on: date | None = None
    workload_minutes: int | None = Field(default=None, ge=0)
    provider: str | None = Field(default=None, max_length=160)
    external_identifier: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class EmployeeQualificationUpdate(BaseModel):
    qualification_id: UUID | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    workload_minutes: int | None = Field(default=None, ge=0)
    provider: str | None = Field(default=None, max_length=160)
    external_identifier: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class EmployeeAuthorizationCreate(BaseModel):
    authorization_id: UUID
    scope_value: str | None = Field(default=None, max_length=160)
    issued_on: date
    expires_on: date | None = None


class EmployeeAuthorizationUpdate(BaseModel):
    authorization_id: UUID | None = None
    scope_value: str | None = Field(default=None, max_length=160)
    issued_on: date | None = None
    expires_on: date | None = None


class EmployeeAvailabilityCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    status: str = Field(min_length=1, max_length=32)


class EmployeeAvailabilityUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)


class EmployeeAssignmentCreate(BaseModel):
    operation_id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str = Field(min_length=1, max_length=32)


class EmployeeAssignmentUpdate(BaseModel):
    operation_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)


class EmployeeCostCreate(BaseModel):
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    hourly_cost_cents: int = Field(ge=0)
    travel_cost_cents: int = Field(default=0, ge=0)
    effective_from: date
    effective_to: date | None = None


class EmployeeCostUpdate(BaseModel):
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    hourly_cost_cents: int | None = Field(default=None, ge=0)
    travel_cost_cents: int | None = Field(default=None, ge=0)
    effective_from: date | None = None
    effective_to: date | None = None


class EmployeeCompetencyCreate(BaseModel):
    competency_id: UUID
    level: int = Field(ge=0)
    assessed_on: date


class EmployeeCompetencyUpdate(BaseModel):
    competency_id: UUID | None = None
    level: int | None = Field(default=None, ge=0)
    assessed_on: date | None = None


class EmployeeRestrictionCreate(BaseModel):
    restriction_id: UUID
    scope_value: str | None = Field(default=None, max_length=160)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = None


class EmployeeRestrictionUpdate(BaseModel):
    restriction_id: UUID | None = None
    scope_value: str | None = Field(default=None, max_length=160)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = None
