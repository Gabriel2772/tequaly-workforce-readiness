from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import require_write_actor
from app.db.base import Base
from app.workforce.commands import (
    DuplicateEmployeeError,
    EmployeeCommandService,
    EmployeeNotFoundForUpdateError,
    InvalidPeriodError,
    ProfileRecordNotFoundError,
    UnknownReferenceError,
    UnknownRoleError,
)
from app.workforce.profile_service import EmployeeNotFoundError, EmployeeProfileService
from app.workforce.reference_service import (
    DuplicateReferenceError,
    ReferenceNotFoundError,
    WorkforceReferenceService,
)
from app.workforce.repository import EmployeeListFilters, SQLAlchemyEmployeeRepository
from app.workforce.schemas import (
    AuthorizationCreate,
    AuthorizationReference,
    AuthorizationUpdate,
    CreatedRecord,
    EmployeeAssignmentCreate,
    EmployeeAssignmentUpdate,
    EmployeeAuthorizationCreate,
    EmployeeAuthorizationUpdate,
    EmployeeAvailabilityCreate,
    EmployeeAvailabilityUpdate,
    EmployeeCompetencyCreate,
    EmployeeCompetencyUpdate,
    EmployeeCostCreate,
    EmployeeCostUpdate,
    EmployeeCreate,
    EmployeeProfileVector,
    EmployeeQualificationCreate,
    EmployeeQualificationUpdate,
    EmployeeRestrictionCreate,
    EmployeeRestrictionUpdate,
    EmployeeUpdate,
    EmployeeWriteResult,
    OperationalRestrictionCreate,
    OperationalRestrictionReference,
    OperationalRestrictionUpdate,
    PaginatedAuthorizations,
    PaginatedEmployees,
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

router = APIRouter(prefix="/employees", tags=["employees"])
reference_router = APIRouter(tags=["workforce references"])


def request_session(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session


@router.get("", response_model=PaginatedEmployees)
def list_employees(
    session: Annotated[Session, Depends(request_session)],
    query: str | None = None,
    role_id: UUID | None = None,
    qualification_id: UUID | None = None,
    employee_status: str | None = Query(default=None, alias="status"),
    base_id: str | None = None,
    available_from: datetime | None = None,
    available_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedEmployees:
    repository = SQLAlchemyEmployeeRepository(session)
    return repository.list_employees(
        EmployeeListFilters(
            query=query,
            role_id=role_id,
            qualification_id=qualification_id,
            status=employee_status,
            base_id=base_id,
            available_from=available_from,
            available_to=available_to,
        ),
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=EmployeeWriteResult, status_code=status.HTTP_201_CREATED)
def create_employee(
    command: EmployeeCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> EmployeeWriteResult:
    try:
        employee = EmployeeCommandService(session, actor_id=actor_id).create_employee(command)
        session.commit()
    except DuplicateEmployeeError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number already exists",
        ) from error
    except UnknownRoleError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown canonical role",
        ) from error
    return EmployeeWriteResult(
        id=employee.id,
        employee_number=employee.employee_number,
        updated_at=employee.updated_at,
    )


@router.patch("/{employee_id}", response_model=EmployeeWriteResult)
def update_employee(
    employee_id: UUID,
    command: EmployeeUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> EmployeeWriteResult:
    try:
        employee = EmployeeCommandService(session, actor_id=actor_id).update_employee(
            employee_id, command
        )
        session.commit()
    except EmployeeNotFoundForUpdateError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        ) from error
    except (UnknownReferenceError, InvalidPeriodError) as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except UnknownRoleError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown canonical role",
        ) from error
    return EmployeeWriteResult(
        id=employee.id,
        employee_number=employee.employee_number,
        updated_at=employee.updated_at,
    )


def _create_profile_record(
    session: Session,
    action: Callable[[], UUID],
) -> CreatedRecord:
    try:
        record_id = action()
        session.commit()
        return CreatedRecord(id=record_id)
    except EmployeeNotFoundForUpdateError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        ) from error


def _update_profile_record(
    session: Session,
    action: Callable[[], UUID],
) -> CreatedRecord:
    try:
        record_id = action()
        session.commit()
        return CreatedRecord(id=record_id)
    except ProfileRecordNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile record not found",
        ) from error
    except (UnknownReferenceError, InvalidPeriodError) as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.post(
    "/{employee_id}/qualifications",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_qualification(
    employee_id: UUID,
    command: EmployeeQualificationCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_qualification(employee_id, command))


@router.patch("/{employee_id}/qualifications/{record_id}", response_model=CreatedRecord)
def update_employee_qualification(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeQualificationUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_qualification(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/authorizations",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_authorization(
    employee_id: UUID,
    command: EmployeeAuthorizationCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_authorization(employee_id, command))


@router.patch("/{employee_id}/authorizations/{record_id}", response_model=CreatedRecord)
def update_employee_authorization(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeAuthorizationUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_authorization(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/availability",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_availability(
    employee_id: UUID,
    command: EmployeeAvailabilityCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_availability(employee_id, command))


@router.patch("/{employee_id}/availability/{record_id}", response_model=CreatedRecord)
def update_employee_availability(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeAvailabilityUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_availability(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/assignments",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_assignment(
    employee_id: UUID,
    command: EmployeeAssignmentCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_assignment(employee_id, command))


@router.patch("/{employee_id}/assignments/{record_id}", response_model=CreatedRecord)
def update_employee_assignment(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeAssignmentUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_assignment(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/costs",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_cost(
    employee_id: UUID,
    command: EmployeeCostCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_cost(employee_id, command))


@router.patch("/{employee_id}/costs/{record_id}", response_model=CreatedRecord)
def update_employee_cost(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeCostUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_cost(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/competencies",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_competency(
    employee_id: UUID,
    command: EmployeeCompetencyCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_competency(employee_id, command))


@router.patch("/{employee_id}/competencies/{record_id}", response_model=CreatedRecord)
def update_employee_competency(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeCompetencyUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_competency(employee_id, record_id, command),
    )


@router.post(
    "/{employee_id}/restrictions",
    response_model=CreatedRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_restriction(
    employee_id: UUID,
    command: EmployeeRestrictionCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _create_profile_record(session, lambda: service.add_restriction(employee_id, command))


@router.patch("/{employee_id}/restrictions/{record_id}", response_model=CreatedRecord)
def update_employee_restriction(
    employee_id: UUID,
    record_id: UUID,
    command: EmployeeRestrictionUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CreatedRecord:
    service = EmployeeCommandService(session, actor_id=actor_id)
    return _update_profile_record(
        session,
        lambda: service.update_restriction(employee_id, record_id, command),
    )


@router.get("/{employee_id}/profile", response_model=EmployeeProfileVector)
def get_employee_profile(
    employee_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> EmployeeProfileVector:
    try:
        return EmployeeProfileService(SQLAlchemyEmployeeRepository(session)).get_profile(
            employee_id
        )
    except EmployeeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        ) from error


@reference_router.get("/qualifications", response_model=PaginatedQualifications)
def list_qualifications(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedQualifications:
    return WorkforceReferenceService(session).list_qualifications(page=page, page_size=page_size)


@reference_router.post(
    "/qualifications",
    response_model=QualificationReference,
    status_code=status.HTTP_201_CREATED,
)
def create_qualification(
    command: QualificationCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> QualificationReference:
    try:
        record = WorkforceReferenceService(session, actor_id=actor_id).create_qualification(command)
        session.commit()
    except DuplicateReferenceError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Qualification code already exists",
        ) from error
    return QualificationReference.model_validate(record)


@reference_router.patch(
    "/qualifications/{qualification_id}",
    response_model=QualificationReference,
)
def update_qualification(
    qualification_id: UUID,
    command: QualificationUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> QualificationReference:
    try:
        record = WorkforceReferenceService(session, actor_id=actor_id).update_qualification(
            qualification_id, command
        )
        session.commit()
    except ReferenceNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualification not found",
        ) from error
    return QualificationReference.model_validate(record)


def _commit_reference[ReferenceModelT: Base](
    session: Session,
    action: Callable[[], ReferenceModelT],
) -> ReferenceModelT:
    try:
        record = action()
        session.commit()
        return record
    except DuplicateReferenceError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_reference", "message": "Reference already exists"},
        ) from error
    except ReferenceNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "reference_not_found", "message": "Reference not found"},
        ) from error


@reference_router.get("/roles", response_model=PaginatedRoles)
def list_roles(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedRoles:
    return WorkforceReferenceService(session).list_roles(page=page, page_size=page_size)


@reference_router.post("/roles", response_model=RoleReference, status_code=status.HTTP_201_CREATED)
def create_role(
    command: RoleCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> RoleReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return RoleReference.model_validate(
        _commit_reference(session, lambda: service.create_role(command))
    )


@reference_router.patch("/roles/{role_id}", response_model=RoleReference)
def update_role_reference(
    role_id: UUID,
    command: RoleUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> RoleReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return RoleReference.model_validate(
        _commit_reference(session, lambda: service.update_role(role_id, command))
    )


@reference_router.get("/role-aliases", response_model=PaginatedRoleAliases)
def list_role_aliases(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedRoleAliases:
    return WorkforceReferenceService(session).list_role_aliases(page=page, page_size=page_size)


@reference_router.post(
    "/role-aliases", response_model=RoleAliasReference, status_code=status.HTTP_201_CREATED
)
def create_role_alias(
    command: RoleAliasCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> RoleAliasReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return RoleAliasReference.model_validate(
        _commit_reference(session, lambda: service.create_role_alias(command))
    )


@reference_router.patch("/role-aliases/{alias_id}", response_model=RoleAliasReference)
def update_role_alias_reference(
    alias_id: UUID,
    command: RoleAliasUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> RoleAliasReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return RoleAliasReference.model_validate(
        _commit_reference(session, lambda: service.update_role_alias(alias_id, command))
    )


@reference_router.get("/authorizations", response_model=PaginatedAuthorizations)
def list_authorizations(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedAuthorizations:
    return WorkforceReferenceService(session).list_authorizations(
        page=page, page_size=page_size
    )


@reference_router.post(
    "/authorizations",
    response_model=AuthorizationReference,
    status_code=status.HTTP_201_CREATED,
)
def create_authorization_reference(
    command: AuthorizationCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> AuthorizationReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return AuthorizationReference.model_validate(
        _commit_reference(session, lambda: service.create_authorization(command))
    )


@reference_router.patch(
    "/authorizations/{authorization_id}", response_model=AuthorizationReference
)
def update_authorization_reference(
    authorization_id: UUID,
    command: AuthorizationUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> AuthorizationReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return AuthorizationReference.model_validate(
        _commit_reference(
            session, lambda: service.update_authorization(authorization_id, command)
        )
    )


@reference_router.get("/training-catalog", response_model=PaginatedTrainingCatalog)
def list_training_catalog(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedTrainingCatalog:
    return WorkforceReferenceService(session).list_training_catalog(
        page=page, page_size=page_size
    )


@reference_router.post(
    "/training-catalog",
    response_model=TrainingCatalogReference,
    status_code=status.HTTP_201_CREATED,
)
def create_training_reference(
    command: TrainingCatalogCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> TrainingCatalogReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return TrainingCatalogReference.model_validate(
        _commit_reference(session, lambda: service.create_training(command))
    )


@reference_router.patch(
    "/training-catalog/{training_id}", response_model=TrainingCatalogReference
)
def update_training_reference(
    training_id: UUID,
    command: TrainingCatalogUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> TrainingCatalogReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return TrainingCatalogReference.model_validate(
        _commit_reference(session, lambda: service.update_training(training_id, command))
    )


@reference_router.get("/competencies", response_model=PaginatedTechnicalCompetencies)
def list_competencies(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedTechnicalCompetencies:
    return WorkforceReferenceService(session).list_competencies(
        page=page, page_size=page_size
    )


@reference_router.post(
    "/competencies",
    response_model=TechnicalCompetencyReference,
    status_code=status.HTTP_201_CREATED,
)
def create_competency_reference(
    command: TechnicalCompetencyCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> TechnicalCompetencyReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return TechnicalCompetencyReference.model_validate(
        _commit_reference(session, lambda: service.create_competency(command))
    )


@reference_router.patch(
    "/competencies/{competency_id}", response_model=TechnicalCompetencyReference
)
def update_competency_reference(
    competency_id: UUID,
    command: TechnicalCompetencyUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> TechnicalCompetencyReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return TechnicalCompetencyReference.model_validate(
        _commit_reference(session, lambda: service.update_competency(competency_id, command))
    )


@reference_router.get("/restrictions", response_model=PaginatedOperationalRestrictions)
def list_restrictions(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedOperationalRestrictions:
    return WorkforceReferenceService(session).list_restrictions(
        page=page, page_size=page_size
    )


@reference_router.post(
    "/restrictions",
    response_model=OperationalRestrictionReference,
    status_code=status.HTTP_201_CREATED,
)
def create_restriction_reference(
    command: OperationalRestrictionCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationalRestrictionReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return OperationalRestrictionReference.model_validate(
        _commit_reference(session, lambda: service.create_restriction(command))
    )


@reference_router.patch(
    "/restrictions/{restriction_id}", response_model=OperationalRestrictionReference
)
def update_restriction_reference(
    restriction_id: UUID,
    command: OperationalRestrictionUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationalRestrictionReference:
    service = WorkforceReferenceService(session, actor_id=actor_id)
    return OperationalRestrictionReference.model_validate(
        _commit_reference(
            session, lambda: service.update_restriction(restriction_id, command)
        )
    )
