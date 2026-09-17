from dataclasses import dataclass
from typing import Literal

ExportType = Literal[
    "employees",
    "readiness",
    "gaps",
    "scenarios",
    "training",
    "risk",
    "decision_runs",
]
ExportFormat = Literal["csv", "xlsx"]


@dataclass(frozen=True)
class StreamingExport:
    filename: str
    media_type: str
    content: bytes
