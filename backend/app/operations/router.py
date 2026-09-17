from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_write_actor
from app.operations.repository import OperationRepository
from app.operations.schemas import (
    OperationCreate,
    OperationDetail,
    OperationRequirementUpdate,
    OperationRequirementView,
    OperationRoleDemandUpdate,
    OperationRoleDemandView,
    OperationUpdate,
    OperationView,
    OperationWriteResult,
    PaginatedOperations,
)
from app.operations.service import (
    DuplicateOperationError,
    InvalidOperationPeriodError,
    OperationChildNotFoundError,
    OperationNotFoundError,
    OperationService,
    UnknownOperationReferenceError,
)
from app.workforce.router import request_session

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("", response_model=PaginatedOperations)
def list_operations(
    session: Annotated[Session, Depends(request_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PaginatedOperations:
    return OperationRepository(session).list_operations(page=page, page_size=page_size)


@router.post("", response_model=OperationWriteResult, status_code=status.HTTP_201_CREATED)
def create_operation(
    command: OperationCreate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationWriteResult:
    try:
        operation = OperationService(session, actor_id).create(command)
        session.commit()
    except DuplicateOperationError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_operation", "message": "Operation code already exists"},
        ) from error
    except UnknownOperationReferenceError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "unknown_operation_reference", "message": str(error)},
        ) from error
    return OperationWriteResult(
        id=operation.id,
        code=operation.code,
        updated_at=operation.updated_at,
    )


@router.get("/{operation_id}", response_model=OperationDetail)
def get_operation(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> OperationDetail:
    detail = OperationRepository(session).get_detail(operation_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        )
    return detail


@router.patch("/{operation_id}", response_model=OperationView)
def update_operation(
    operation_id: UUID,
    command: OperationUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationView:
    try:
        operation = OperationService(session, actor_id).update(operation_id, command)
        session.commit()
    except OperationNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        ) from error
    except InvalidOperationPeriodError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_operation_period", "message": str(error)},
        ) from error
    return OperationView.model_validate(operation)


@router.patch(
    "/{operation_id}/demands/{demand_id}",
    response_model=OperationRoleDemandView,
)
def update_operation_demand(
    operation_id: UUID,
    demand_id: UUID,
    command: OperationRoleDemandUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationRoleDemandView:
    try:
        demand = OperationService(session, actor_id).update_demand(
            operation_id, demand_id, command
        )
        session.commit()
    except OperationChildNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_demand_not_found", "message": "Demand not found"},
        ) from error
    except UnknownOperationReferenceError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "unknown_operation_reference", "message": str(error)},
        ) from error
    return OperationRoleDemandView.model_validate(demand)


@router.patch(
    "/{operation_id}/requirements/{requirement_id}",
    response_model=OperationRequirementView,
)
def update_operation_requirement(
    operation_id: UUID,
    requirement_id: UUID,
    command: OperationRequirementUpdate,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OperationRequirementView:
    try:
        requirement = OperationService(session, actor_id).update_requirement(
            operation_id, requirement_id, command
        )
        session.commit()
    except OperationChildNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "operation_requirement_not_found",
                "message": "Requirement not found",
            },
        ) from error
    return OperationRequirementView.model_validate(requirement)


@router.get("/{operation_id}/requirements", response_model=list[OperationRequirementView])
def list_operation_requirements(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> list[OperationRequirementView]:
    return OperationRepository(session).list_requirements(operation_id)
