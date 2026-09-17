from app.fragility.rules import calculate_metric


def test_exact_coverage_is_a_single_point_of_failure() -> None:
    metric = calculate_metric(
        required_count=2,
        eligible_count=2,
        trainable_count=1,
        expiring_count=0,
        allocated_count=0,
        missing_session_count=0,
    )

    assert metric.coverage_ratio == 1.0
    assert metric.redundancy == 0
    assert metric.single_point_of_failure is True


def test_surplus_coverage_reports_redundancy() -> None:
    metric = calculate_metric(
        required_count=2,
        eligible_count=5,
        trainable_count=0,
        expiring_count=1,
        allocated_count=1,
        missing_session_count=0,
    )

    assert metric.coverage_ratio == 2.5
    assert metric.redundancy == 3
    assert metric.single_point_of_failure is False
