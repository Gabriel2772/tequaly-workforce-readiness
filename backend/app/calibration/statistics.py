from decimal import Decimal
from statistics import median, quantiles

from app.calibration.types import RobustEstimate


class InsufficientCalibrationSamplesError(ValueError):
    def __init__(self, sample_size: int, minimum_sample_size: int) -> None:
        self.sample_size = sample_size
        self.minimum_sample_size = minimum_sample_size
        super().__init__(
            f"{sample_size} samples supplied; {minimum_sample_size} required"
        )


def robust_estimate(
    samples: list[Decimal],
    *,
    minimum_sample_size: int = 5,
) -> RobustEstimate:
    if len(samples) < minimum_sample_size:
        raise InsufficientCalibrationSamplesError(
            len(samples), minimum_sample_size
        )
    ordered = sorted(samples)
    quartiles = quantiles(ordered, n=4, method="inclusive")
    return RobustEstimate(
        value=median(ordered),
        sample_size=len(ordered),
        minimum_sample_size=minimum_sample_size,
        confidence_basis="median_iqr",
        interquartile_range=quartiles[2] - quartiles[0],
    )
