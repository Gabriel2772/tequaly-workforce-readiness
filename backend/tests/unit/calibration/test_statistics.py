from decimal import Decimal

from app.calibration.statistics import InsufficientCalibrationSamplesError, robust_estimate


def test_robust_estimate_uses_median_for_skewed_samples() -> None:
    estimate = robust_estimate(
        [
            Decimal("100"),
            Decimal("100"),
            Decimal("110"),
            Decimal("120"),
            Decimal("10000"),
        ]
    )

    assert estimate.value == Decimal("110")
    assert estimate.sample_size == 5
    assert estimate.confidence_basis == "median_iqr"
    assert estimate.minimum_sample_size == 5
    assert estimate.interquartile_range == Decimal("20")


def test_robust_estimate_requires_at_least_five_samples() -> None:
    try:
        robust_estimate([Decimal("100"), Decimal("110"), Decimal("120"), Decimal("130")])
    except InsufficientCalibrationSamplesError as error:
        assert error.sample_size == 4
        assert error.minimum_sample_size == 5
    else:
        raise AssertionError("four samples must not produce a calibration estimate")
