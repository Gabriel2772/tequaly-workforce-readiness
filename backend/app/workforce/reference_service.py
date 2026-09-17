from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.db.base import UUIDPrimaryKeyMixin
from app.decisions.models import AuditEvent
from app.workforce.models import (
    Authorization,
    OperationalRestriction,
    Qualification,
    Role,
    RoleAlias,
    RoleFamily,
    TechnicalCompetency,
    TrainingCatalog,
)
from app.workforce.schemas import (
    AuthorizationCreate,
    AuthorizationReference,
    AuthorizationUpdate,
    OperationalRestrictionCreate,
    OperationalRestrictionReference,
    OperationalRestrictionUpdate,
    PaginatedAuthorizations,
    PaginatedOperationalRestrictions,
    PaginatedQualifications,
    PaginatedRoleAliases,
    PaginatedRoles,
    PaginatedTechnicalCompetencies,
    PaginatedTrainingCatalog,
    QualificationCreate,
    QualificationReference,
    QualificationUpdate,
    RoleAliasCreate,
    RoleAliasReference,
    RoleAliasUpdate,
    RoleCreate,
    RoleReference,
    RoleUpdate,
    TechnicalCompetencyCreate,
    TechnicalCompetencyReference,
    TechnicalCompetencyUpdate,
    TrainingCatalogCreate,
    TrainingCatalogReference,
    TrainingCatalogUpdate,
)

ModelT = TypeVar("ModelT", bound=UUIDPrimaryKeyMixin)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class DuplicateReferenceError(ValueError):
    pass


class ReferenceNotFoundError(LookupError):
    pass


class WorkforceReferenceService:
    def __init__(self, session: Session, actor_id: str = "local-system") -> None:
        self._session = session
        self._actor_id = actor_id

    def list_qualifications(self, *, page: int, page_size: int) -> PaginatedQualifications:
        items, total = self._page(
            Qualification, QualificationReference, Qualification.code, page, page_size
        )
        return PaginatedQualifications(items=items, page=page, page_size=page_size, total=total)

    def create_qualification(self, command: QualificationCreate) -> Qualification:
        record = Qualification(
            code=self._new_code(Qualification, command.code),
            name=command.name.strip(),
            category=command.category.strip(),
            method=command.method,
            level=command.level,
            validity_days=command.validity_days,
            active=command.active,
        )
        return self._add_reference(record, "qualification")

    def update_qualification(
        self, qualification_id: UUID, command: QualificationUpdate
    ) -> Qualification:
        return self._update_reference(
            Qualification, qualification_id, command, "qualification"
        )

    def list_roles(self, *, page: int, page_size: int) -> PaginatedRoles:
        items, total = self._page(Role, RoleReference, Role.code, page, page_size)
        return PaginatedRoles(items=items, page=page, page_size=page_size, total=total)

    def create_role(self, command: RoleCreate) -> Role:
        self._require(RoleFamily, command.family_id)
        record = Role(
            family_id=command.family_id,
            code=self._new_code(Role, command.code),
            name=command.name.strip(),
            active=command.active,
        )
        return self._add_reference(record, "role")

    def update_role(self, role_id: UUID, command: RoleUpdate) -> Role:
        if command.family_id is not None:
            self._require(RoleFamily, command.family_id)
        return self._update_reference(Role, role_id, command, "role")

    def list_role_aliases(self, *, page: int, page_size: int) -> PaginatedRoleAliases:
        items, total = self._page(
            RoleAlias, RoleAliasReference, RoleAlias.normalized_title, page, page_size
        )
        return PaginatedRoleAliases(items=items, page=page, page_size=page_size, total=total)

    def create_role_alias(self, command: RoleAliasCreate) -> RoleAlias:
        self._require(Role, command.role_id)
        normalized = command.normalized_title.strip().lower()
        self._ensure_unique(RoleAlias, "normalized_title", normalized)
        record = RoleAlias(
            role_id=command.role_id,
            source_title=command.source_title.strip(),
            normalized_title=normalized,
            active=command.active,
        )
        return self._add_reference(record, "role_alias")

    def update_role_alias(self, alias_id: UUID, command: RoleAliasUpdate) -> RoleAlias:
        if command.role_id is not None:
            self._require(Role, command.role_id)
        updates = command.model_dump(exclude_unset=True)
        if "normalized_title" in updates:
            normalized = str(updates["normalized_title"]).strip().lower()
            self._ensure_unique(RoleAlias, "normalized_title", normalized, exclude_id=alias_id)
            updates["normalized_title"] = normalized
        return self._update_reference(
            RoleAlias, alias_id, command, "role_alias", updates=updates
        )

    def list_authorizations(self, *, page: int, page_size: int) -> PaginatedAuthorizations:
        items, total = self._page(
            Authorization, AuthorizationReference, Authorization.code, page, page_size
        )
        return PaginatedAuthorizations(items=items, page=page, page_size=page_size, total=total)

    def create_authorization(self, command: AuthorizationCreate) -> Authorization:
        record = Authorization(
            code=self._new_code(Authorization, command.code),
            name=command.name.strip(),
            scope_type=command.scope_type.strip(),
            active=command.active,
        )
        return self._add_reference(record, "authorization")

    def update_authorization(
        self, authorization_id: UUID, command: AuthorizationUpdate
    ) -> Authorization:
        return self._update_reference(
            Authorization, authorization_id, command, "authorization"
        )

    def list_training_catalog(self, *, page: int, page_size: int) -> PaginatedTrainingCatalog:
        items, total = self._page(
            TrainingCatalog, TrainingCatalogReference, TrainingCatalog.code, page, page_size
        )
        return PaginatedTrainingCatalog(items=items, page=page, page_size=page_size, total=total)

    def create_training(self, command: TrainingCatalogCreate) -> TrainingCatalog:
        self._require(Qualification, command.qualification_id)
        record = TrainingCatalog(
            code=self._new_code(TrainingCatalog, command.code),
            name=command.name.strip(),
            qualification_id=command.qualification_id,
            duration_minutes=command.duration_minutes,
            cost_cents=command.cost_cents,
            active=command.active,
        )
        return self._add_reference(record, "training_catalog")

    def update_training(
        self, training_id: UUID, command: TrainingCatalogUpdate
    ) -> TrainingCatalog:
        if command.qualification_id is not None:
            self._require(Qualification, command.qualification_id)
        return self._update_reference(
            TrainingCatalog, training_id, command, "training_catalog"
        )

    def list_competencies(
        self, *, page: int, page_size: int
    ) -> PaginatedTechnicalCompetencies:
        items, total = self._page(
            TechnicalCompetency,
            TechnicalCompetencyReference,
            TechnicalCompetency.code,
            page,
            page_size,
        )
        return PaginatedTechnicalCompetencies(
            items=items, page=page, page_size=page_size, total=total
        )

    def create_competency(self, command: TechnicalCompetencyCreate) -> TechnicalCompetency:
        record = TechnicalCompetency(
            code=self._new_code(TechnicalCompetency, command.code),
            name=command.name.strip(),
            scale_max=command.scale_max,
            active=command.active,
        )
        return self._add_reference(record, "technical_competency")

    def update_competency(
        self, competency_id: UUID, command: TechnicalCompetencyUpdate
    ) -> TechnicalCompetency:
        return self._update_reference(
            TechnicalCompetency, competency_id, command, "technical_competency"
        )

    def list_restrictions(
        self, *, page: int, page_size: int
    ) -> PaginatedOperationalRestrictions:
        items, total = self._page(
            OperationalRestriction,
            OperationalRestrictionReference,
            OperationalRestriction.code,
            page,
            page_size,
        )
        return PaginatedOperationalRestrictions(
            items=items, page=page, page_size=page_size, total=total
        )

    def create_restriction(
        self, command: OperationalRestrictionCreate
    ) -> OperationalRestriction:
        record = OperationalRestriction(
            code=self._new_code(OperationalRestriction, command.code),
            name=command.name.strip(),
            hard_constraint=command.hard_constraint,
            active=command.active,
        )
        return self._add_reference(record, "operational_restriction")

    def update_restriction(
        self, restriction_id: UUID, command: OperationalRestrictionUpdate
    ) -> OperationalRestriction:
        return self._update_reference(
            OperationalRestriction,
            restriction_id,
            command,
            "operational_restriction",
        )

    def _page(
        self,
        model: type[ModelT],
        schema: type[SchemaT],
        order_column: InstrumentedAttribute[Any],
        page: int,
        page_size: int,
    ) -> tuple[list[SchemaT], int]:
        total = self._session.scalar(select(func.count()).select_from(model)) or 0
        records = self._session.scalars(
            select(model).order_by(order_column).offset((page - 1) * page_size).limit(page_size)
        )
        return [schema.model_validate(record) for record in records], total

    def _new_code(self, model: type[ModelT], value: str) -> str:
        normalized = value.strip().upper()
        self._ensure_unique(model, "code", normalized)
        return normalized

    def _ensure_unique(
        self,
        model: type[ModelT],
        field: str,
        value: object,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        model_id = model.id
        statement = select(model_id).where(getattr(model, field) == value)
        if exclude_id is not None:
            statement = statement.where(model_id != exclude_id)
        if self._session.scalar(statement) is not None:
            raise DuplicateReferenceError(str(value))

    def _require(self, model: type[ModelT], record_id: UUID) -> ModelT:
        record = self._session.get(model, record_id)
        if record is None:
            raise ReferenceNotFoundError(f"{model.__name__}:{record_id}")
        return record

    def _add_reference(self, record: ModelT, aggregate_type: str) -> ModelT:
        self._session.add(record)
        self._session.flush()
        self._audit(f"{aggregate_type}.created", aggregate_type, record.id)
        return record

    def _update_reference(
        self,
        model: type[ModelT],
        record_id: UUID,
        command: BaseModel,
        aggregate_type: str,
        *,
        updates: dict[str, object] | None = None,
    ) -> ModelT:
        record = self._require(model, record_id)
        changed = command.model_dump(exclude_unset=True) if updates is None else updates
        for field, value in changed.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(record, field, value)
        self._session.flush()
        self._audit(
            f"{aggregate_type}.updated",
            aggregate_type,
            record.id,
            payload={"changed_fields": sorted(changed)},
        )
        return record

    def _audit(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID,
        *,
        payload: dict[str, object] | None = None,
    ) -> None:
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                payload=payload or {},
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
