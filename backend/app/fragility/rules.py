from app.fragility.types import FragilityMetric, RiskAssessment, RiskExplanation, RiskSeverity


def calculate_metric(
    *,
    required_count: int,
    eligible_count: int,
    trainable_count: int,
    expiring_count: int,
    allocated_count: int,
    missing_session_count: int,
) -> FragilityMetric:
    if required_count <= 0:
        raise ValueError("required_count must be positive")
    counts = (
        eligible_count,
        trainable_count,
        expiring_count,
        allocated_count,
        missing_session_count,
    )
    if any(value < 0 for value in counts):
        raise ValueError("fragility counts cannot be negative")
    redundancy = max(eligible_count - required_count, 0)
    return FragilityMetric(
        required_count=required_count,
        eligible_count=eligible_count,
        trainable_count=trainable_count,
        expiring_count=expiring_count,
        allocated_count=allocated_count,
        missing_session_count=missing_session_count,
        coverage_ratio=round(eligible_count / required_count, 4),
        redundancy=redundancy,
        single_point_of_failure=(eligible_count == required_count),
    )


_SEVERITY_RANK: dict[RiskSeverity, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def assess_risk(metric: FragilityMetric) -> RiskAssessment:
    explanations: list[RiskExplanation] = []
    severity: RiskSeverity = "low"

    def add(
        level: RiskSeverity,
        code: str,
        message: str,
        *,
        threshold: int | float,
        observed: int | float,
    ) -> None:
        nonlocal severity
        if _SEVERITY_RANK[level] > _SEVERITY_RANK[severity]:
            severity = level
        explanations.append(
            RiskExplanation(
                code=code,
                message=message,
                threshold=threshold,
                observed=observed,
            )
        )

    if metric.eligible_count < metric.required_count:
        add(
            "critical",
            "coverage_below_required",
            (
                f"{metric.eligible_count} pessoa(s) elegível(is) para "
                f"{metric.required_count} vaga(s)."
            ),
            threshold=metric.required_count,
            observed=metric.eligible_count,
        )
    elif metric.single_point_of_failure:
        add(
            "high",
            "single_point_of_failure",
            "A cobertura é exata; a indisponibilidade de uma pessoa descobre a demanda.",
            threshold=1,
            observed=metric.redundancy,
        )

    effective_after_allocations = max(metric.eligible_count - metric.allocated_count, 0)
    if metric.allocated_count and effective_after_allocations < metric.required_count:
        add(
            "high",
            "allocation_pressure",
            "Alocações concorrentes reduzem a cobertura abaixo da demanda.",
            threshold=metric.required_count,
            observed=effective_after_allocations,
        )
    if metric.expiring_count:
        add(
            "medium",
            "qualification_expiry_pressure",
            "Qualificações exigidas vencem antes da mobilização.",
            threshold=0,
            observed=metric.expiring_count,
        )
    if metric.missing_session_count:
        add(
            "medium",
            "training_without_viable_session",
            "Pessoas treináveis não possuem turma viável antes da mobilização.",
            threshold=0,
            observed=metric.missing_session_count,
        )

    return RiskAssessment(
        severity=severity,
        reason_codes=[explanation.code for explanation in explanations],
        explanations=explanations,
    )
