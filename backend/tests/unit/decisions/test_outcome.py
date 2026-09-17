from datetime import UTC, datetime

from app.decisions.outcome_service import calculate_outcome_comparison


def test_outcome_comparison_calculates_cost_delay_substitutions_and_training() -> None:
    comparison = calculate_outcome_comparison(
        predicted_cost_cents=100_000,
        actual_cost_cents=125_000,
        predicted_ready_at=datetime(2026, 10, 1, 8, tzinfo=UTC),
        actual_ready_at=datetime(2026, 10, 1, 10, 30, tzinfo=UTC),
        planned_training_count=3,
        performed_training_count=2,
        substitution_count=1,
    )

    assert comparison.cost.predicted_cents == 100_000
    assert comparison.cost.actual_cents == 125_000
    assert comparison.cost.variance_cents == 25_000
    assert comparison.cost.variance_percent == 25.0
    assert comparison.readiness.variance_minutes == 150
    assert comparison.readiness.status == "delayed"
    assert comparison.assignments.substitution_count == 1
    assert comparison.training.planned_count == 3
    assert comparison.training.performed_count == 2
    assert comparison.training.unperformed_count == 1
    assert comparison.training.completion_percent == 66.67


def test_outcome_comparison_reports_advance_and_undefined_percentages() -> None:
    comparison = calculate_outcome_comparison(
        predicted_cost_cents=0,
        actual_cost_cents=0,
        predicted_ready_at=datetime(2026, 10, 1, 8, tzinfo=UTC),
        actual_ready_at=datetime(2026, 10, 1, 7, tzinfo=UTC),
        planned_training_count=0,
        performed_training_count=0,
        substitution_count=0,
    )

    assert comparison.cost.variance_percent is None
    assert comparison.readiness.variance_minutes == -60
    assert comparison.readiness.status == "advanced"
    assert comparison.training.completion_percent is None
