from time import perf_counter

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo, stable_demo_id
from app.eligibility.run_service import EligibilityRunService
from app.operations import models as operation_models  # noqa: F401
from app.optimization.service import OptimizationService
from app.optimization.types import Objective
from app.workforce import models as workforce_models  # noqa: F401


def test_full_operation_eligibility_for_3_000_people_finishes_under_15_seconds() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    dataset = generate_demo_dataset(seed=84, employee_count=3_000)
    operation_code = dataset.operations[0].code
    operation_id = stable_demo_id(dataset.seed, "operation", operation_code)

    with Session(engine) as session:
        seed_demo(session, dataset)
        session.commit()

        started_at = perf_counter()
        result = EligibilityRunService(session, "benchmark@example.com").run_operation(operation_id)
        elapsed_seconds = perf_counter() - started_at
        scenarios = [
            OptimizationService(session, "benchmark@example.com").optimize(operation_id, objective)
            for objective in Objective
        ]

    assert result.candidate_count < 3_000
    assert result.evaluated_count == len(result.results)
    assert result.runtime_ms < 15_000
    assert elapsed_seconds < 15
    assert all(scenario.runtime_ms < 30_000 for scenario in scenarios)
    engine.dispose()
