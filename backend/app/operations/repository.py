from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.operations.models import Operation, OperationRequirement, OperationRoleDemand
from app.operations.schemas import (
    OperationDetail,
    OperationRequirementView,
    OperationRoleDemandView,
    OperationView,
    PaginatedOperations,
)


class OperationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_requirements(self, operation_id: UUID) -> list[OperationRequirementView]:
        records = self._session.scalars(
            select(OperationRequirement)
            .where(OperationRequirement.operation_id == operation_id)
            .order_by(OperationRequirement.code)
        )
        return [OperationRequirementView.model_validate(record) for record in records]

    def list_operations(self, *, page: int, page_size: int) -> PaginatedOperations:
        total = self._session.scalar(select(func.count()).select_from(Operation)) or 0
        records = self._session.scalars(
            select(Operation)
            .order_by(Operation.starts_at.desc(), Operation.code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return PaginatedOperations(
            items=[OperationView.model_validate(record) for record in records],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_detail(self, operation_id: UUID) -> OperationDetail | None:
        operation = self._session.get(Operation, operation_id)
        if operation is None:
            return None
        demands = self._session.scalars(
            select(OperationRoleDemand)
            .where(OperationRoleDemand.operation_id == operation_id)
            .order_by(OperationRoleDemand.priority, OperationRoleDemand.shift_code)
        )
        requirements = self.list_requirements(operation_id)
        return OperationDetail(
            **OperationView.model_validate(operation).model_dump(),
            demands=[OperationRoleDemandView.model_validate(record) for record in demands],
            requirements=requirements,
        )
