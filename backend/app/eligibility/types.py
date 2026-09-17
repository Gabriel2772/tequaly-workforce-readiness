from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.eligibility.reason_codes import REASON_MESSAGES, EligibilityReasonCode


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    TRAINABLE = "TRAINABLE"
    INELIGIBLE = "INELIGIBLE"


@dataclass(frozen=True)
class QualificationFact:
    qualification_id: UUID
    expires_on: datetime | None


@dataclass(frozen=True)
class AvailabilityWindow:
    starts_at: datetime
    ends_at: datetime
    status: str = "available"


@dataclass(frozen=True)
class AssignmentWindow:
    assignment_id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str = "confirmed"


@dataclass(frozen=True)
class AuthorizationFact:
    authorization_id: UUID
    expires_on: datetime | None
    scope_value: str | None = None


@dataclass(frozen=True)
class TrainingOption:
    qualification_id: UUID
    training_catalog_id: UUID
    completes_at: datetime


@dataclass(frozen=True)
class OperationalRestrictionFact:
    restriction_id: UUID
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    hard_constraint: bool = True
    scope_value: str | None = None


@dataclass(frozen=True)
class EmployeeEligibilityContext:
    employee_id: UUID
    active: bool
    role_id: UUID
    qualifications: tuple[QualificationFact, ...] = ()
    availability: tuple[AvailabilityWindow, ...] = ()
    assignments: tuple[AssignmentWindow, ...] = ()
    authorizations: tuple[AuthorizationFact, ...] = ()
    training_options: tuple[TrainingOption, ...] = ()
    restrictions: tuple[OperationalRestrictionFact, ...] = ()
    experience_months: int = 0


@dataclass(frozen=True)
class OperationEligibilityContext:
    starts_at: datetime
    ends_at: datetime
    mobilization_deadline: datetime | None


@dataclass(frozen=True)
class DemandEligibilityContext:
    demand_id: UUID
    compatible_role_ids: frozenset[UUID]
    required_qualification_ids: frozenset[UUID] = frozenset()
    trainable_qualification_ids: frozenset[UUID] = frozenset()
    required_authorization_ids: frozenset[UUID] = frozenset()
    applicable_restriction_ids: frozenset[UUID] = frozenset()
    minimum_experience_months: int = 0


@dataclass(frozen=True)
class EligibilityReason:
    code: EligibilityReasonCode
    details: dict[str, object]

    @property
    def message(self) -> str:
        return REASON_MESSAGES[self.code]


@dataclass(frozen=True)
class EligibilityResult:
    status: EligibilityStatus
    eligible: bool
    reasons: tuple[EligibilityReason, ...]
    gaps: tuple[dict[str, object], ...] = ()
    required_training: tuple[UUID, ...] = ()
    ready_at: datetime | None = None
