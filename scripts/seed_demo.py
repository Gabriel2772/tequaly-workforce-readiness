from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import create_session_factory  # noqa: E402
from app.demo.generator import generate_demo_dataset  # noqa: E402
from app.demo.seed import seed_demo  # noqa: E402


def run_seed(*, seed: int, employee_count: int) -> None:
    dataset = generate_demo_dataset(seed=seed, employee_count=employee_count)
    engine, factory = create_session_factory()
    try:
        with factory.begin() as session:
            summary = seed_demo(session, dataset)
    finally:
        engine.dispose()

    print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic TWR demo data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--employees", type=int, default=2_200)
    arguments = parser.parse_args()
    run_seed(seed=arguments.seed, employee_count=arguments.employees)


if __name__ == "__main__":
    main()
