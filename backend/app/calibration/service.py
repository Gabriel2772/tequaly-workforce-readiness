from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.calibration.statistics import (
    InsufficientCalibrationSamplesError,
    robust_estimate,
)
from app.calibration.types import (
    CalibrationParameterName,
    CalibrationParameterView,
    CalibrationSuggestionView,
)
from app.decisions.models import (
    AuditEvent,
    CalibrationParameter,
    CalibrationSuggestion,
    DecisionOutcome,
)


class CalibrationSuggestionNotFoundError(LookupError):
    pass


class CalibrationConfirmationRequiredError(RuntimeError):
    pass


class CalibrationSuggestionAlreadyAppliedError(RuntimeError):
    pass


class CalibrationService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def suggest(
        self,
        parameter: CalibrationParameterName,
        category: str,
    ) -> CalibrationSuggestionView:
        normalized_category = category.strip().lower()
        samples = self._observation_samples(parameter, normalized_category)
        estimate = robust_estimate(samples)
        parameter_key = f"{parameter}:{normalized_category}"
        current = self._session.scalar(
            select(CalibrationParameter)
            .where(CalibrationParameter.name == parameter_key)
            .order_by(CalibrationParameter.created_at.desc(), CalibrationParameter.id.desc())
            .limit(1)
        )
        current_value = current.value if current is not None else Decimal(0)
        rationale = (
            f"Mediana de {estimate.sample_size} observacoes; "
            f"IQR {estimate.interquartile_range}."
        )
        suggestion = CalibrationSuggestion(
            parameter_name=parameter,
            category=normalized_category,
            current_value=current_value,
            proposed_value=estimate.value,
            sample_size=estimate.sample_size,
            confidence_basis=estimate.confidence_basis,
            interquartile_range=estimate.interquartile_range,
            rationale=rationale,
            status="pending",
            created_by=self._actor_id,
        )
        self._session.add(suggestion)
        self._session.flush()
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="calibration.suggestion_created",
                aggregate_type="calibration_suggestion",
                aggregate_id=suggestion.id,
                payload={
                    "parameter": parameter,
                    "category": normalized_category,
                    "sample_size": estimate.sample_size,
                    "proposed_value": str(estimate.value),
                },
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        return self._suggestion_view(suggestion)

    def apply_suggestion(
        self,
        suggestion_id: UUID,
        *,
        confirmed: bool,
    ) -> CalibrationParameterView:
        suggestion = self._session.get(CalibrationSuggestion, suggestion_id)
        if suggestion is None:
            raise CalibrationSuggestionNotFoundError(str(suggestion_id))
        if not confirmed:
            raise CalibrationConfirmationRequiredError(str(suggestion_id))
        if suggestion.status != "pending":
            raise CalibrationSuggestionAlreadyAppliedError(str(suggestion_id))
        parameter_key = f"{suggestion.parameter_name}:{suggestion.category}"
        version_count = self._session.scalar(
            select(func.count())
            .select_from(CalibrationParameter)
            .where(CalibrationParameter.name == parameter_key)
        ) or 0
        parameter = CalibrationParameter(
            name=parameter_key,
            version=f"v{version_count + 1}",
            value=suggestion.proposed_value,
            rationale=suggestion.rationale,
        )
        self._session.add(parameter)
        self._session.flush()
        applied_at = datetime.now(UTC)
        suggestion.status = "applied"
        suggestion.applied_by = self._actor_id
        suggestion.applied_at = applied_at
        suggestion.applied_parameter_id = parameter.id
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="calibration.suggestion_applied",
                aggregate_type="calibration_suggestion",
                aggregate_id=suggestion.id,
                payload={
                    "parameter_id": str(parameter.id),
                    "name": parameter.name,
                    "version": parameter.version,
                    "value": str(parameter.value),
                },
                occurred_at=applied_at,
            )
        )
        self._session.flush()
        return CalibrationParameterView.model_validate(parameter, from_attributes=True)

    def _observation_samples(
        self,
        parameter: CalibrationParameterName,
        category: str,
    ) -> list[Decimal]:
        samples: list[Decimal] = []
        for outcome in self._session.scalars(select(DecisionOutcome)):
            raw_observations = outcome.outcome_metrics.get(
                "calibration_observations", []
            )
            if not isinstance(raw_observations, list):
                continue
            for observation in raw_observations:
                if not isinstance(observation, dict):
                    continue
                if (
                    observation.get("parameter") != parameter
                    or str(observation.get("category", "")).strip().lower()
                    != category
                ):
                    continue
                try:
                    samples.append(Decimal(str(observation["value"])))
                except (InvalidOperation, KeyError):
                    continue
        return samples

    @staticmethod
    def _suggestion_view(
        suggestion: CalibrationSuggestion,
    ) -> CalibrationSuggestionView:
        return CalibrationSuggestionView.model_validate(
            suggestion, from_attributes=True
        )


__all__ = [
    "CalibrationConfirmationRequiredError",
    "CalibrationService",
    "CalibrationSuggestionAlreadyAppliedError",
    "CalibrationSuggestionNotFoundError",
    "InsufficientCalibrationSamplesError",
]
