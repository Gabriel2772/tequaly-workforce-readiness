from typing import Literal

from pydantic import BaseModel


class DataQualityIssue(BaseModel):
    code: str
    label: str
    count: int
    severity: Literal["low", "medium", "high"]
    action: str


class DataQualityOverview(BaseModel):
    active_employees: int
    complete_profiles: int
    completeness_percent: float | None
    issues: list[DataQualityIssue]
    source_mode: Literal["synthetic_demo", "operational"]
