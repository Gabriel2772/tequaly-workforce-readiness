from datetime import UTC, datetime
from uuid import UUID

from app.training.investment_model import (
    InvestmentOpportunity,
    InvestmentProblem,
    solve_investment,
)


def _uuid(value: int) -> UUID:
    return UUID(int=value)


def test_investment_never_exceeds_budget_and_prefers_higher_weighted_coverage() -> None:
    shared_completion = datetime(2026, 11, 1, tzinfo=UTC)
    two_positions = InvestmentOpportunity(
        employee_id=_uuid(1),
        qualification_id=_uuid(11),
        training_catalog_id=_uuid(21),
        training_session_id=_uuid(31),
        completes_at=shared_completion,
        cost_cents=50_000,
        coverage_gain=200,
        unlocked_position_count=2,
        benefited_operation_ids=(_uuid(41),),
    )
    one_position = InvestmentOpportunity(
        employee_id=_uuid(2),
        qualification_id=_uuid(12),
        training_catalog_id=_uuid(22),
        training_session_id=_uuid(32),
        completes_at=shared_completion,
        cost_cents=50_000,
        coverage_gain=100,
        unlocked_position_count=1,
        benefited_operation_ids=(_uuid(42),),
    )

    result = solve_investment(
        InvestmentProblem(
            budget_cents=50_000,
            opportunities=(one_position, two_positions),
        )
    )

    assert result.total_cost_cents <= 50_000
    assert result.selected == (two_positions,)
    assert result.coverage_gain == 200
    assert result.unlocked_position_count == 2


def test_investment_never_selects_overlapping_sessions_for_same_employee() -> None:
    first_session = _uuid(31)
    second_session = _uuid(32)
    employee_id = _uuid(1)
    first = InvestmentOpportunity(
        employee_id=employee_id,
        qualification_id=_uuid(11),
        training_catalog_id=_uuid(21),
        training_session_id=first_session,
        completes_at=datetime(2026, 11, 1, 17, tzinfo=UTC),
        cost_cents=50_000,
        coverage_gain=100,
        unlocked_position_count=1,
        benefited_operation_ids=(_uuid(41),),
    )
    second = InvestmentOpportunity(
        employee_id=employee_id,
        qualification_id=_uuid(12),
        training_catalog_id=_uuid(22),
        training_session_id=second_session,
        completes_at=datetime(2026, 11, 1, 18, tzinfo=UTC),
        cost_cents=50_000,
        coverage_gain=100,
        unlocked_position_count=1,
        benefited_operation_ids=(_uuid(42),),
    )

    result = solve_investment(
        InvestmentProblem(
            budget_cents=100_000,
            opportunities=(first, second),
            session_periods=(
                (
                    first_session,
                    datetime(2026, 11, 1, 9, tzinfo=UTC),
                    datetime(2026, 11, 1, 17, tzinfo=UTC),
                ),
                (
                    second_session,
                    datetime(2026, 11, 1, 10, tzinfo=UTC),
                    datetime(2026, 11, 1, 18, tzinfo=UTC),
                ),
            ),
        )
    )

    assert len(result.selected) == 1
    assert result.coverage_gain == 100
