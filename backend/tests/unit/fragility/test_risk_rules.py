from app.fragility.rules import assess_risk, calculate_metric


def test_uncovered_demand_is_critical_and_explains_threshold() -> None:
    metric = calculate_metric(
        required_count=4,
        eligible_count=2,
        trainable_count=1,
        expiring_count=0,
        allocated_count=0,
        missing_session_count=1,
    )

    assessment = assess_risk(metric)

    assert assessment.severity == "critical"
    assert assessment.reason_codes[0] == "coverage_below_required"
    explanation = assessment.explanations[0]
    assert explanation.threshold == 4
    assert explanation.observed == 2
    assert "2 pessoa(s) eleg�vel(is) para 4 vaga(s)" in explanation.message


def test_exact_coverage_is_high_risk_even_when_demand_is_covered() -> None:
    assessment = assess_risk(
        calculate_metric(
            required_count=2,
            eligible_count=2,
            trainable_count=0,
            expiring_count=0,
            allocated_count=0,
            missing_session_count=0,
        )
    )

    assert assessment.severity == "high"
    assert "single_point_of_failure" in assessment.reason_codes
