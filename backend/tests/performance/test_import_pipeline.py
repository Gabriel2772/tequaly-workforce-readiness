import base64
from time import perf_counter

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.imports.commit_service import ImportCommitService
from app.imports.preview_service import ImportPreviewService
from app.imports.types import ImportPreviewCommand
from app.workforce.models import Employee


def test_three_thousand_employee_dry_run_and_commit_stay_within_poc_target() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    dataset = generate_demo_dataset(seed=42, employee_count=20)
    role_code = dataset.canonical_roles[0].code
    header = "Matr�cula,Nome,Email,Cargo,Base,N�vel,Admiss�o,Ativo"
    rows = [
        f"PERF-{index:05d},Pessoa {index:05d},perf-{index:05d}@example.com,"
        f"{role_code},Curitiba,pleno,2026-01-10,sim"
        for index in range(3_000)
    ]
    content = "\n".join([header, *rows]).encode()

    with Session(engine) as session:
        seed_demo(session, dataset)
        session.commit()
        preview_started = perf_counter()
        preview = ImportPreviewService(session, "benchmark").preview(
            ImportPreviewCommand(
                contract="employees",
                filename="employees.csv",
                content_base64=base64.b64encode(content).decode(),
            )
        )
        session.commit()
        preview_seconds = perf_counter() - preview_started

        commit_started = perf_counter()
        summary = ImportCommitService(session, "benchmark").commit(
            preview.token, confirmed=True
        )
        session.commit()
        commit_seconds = perf_counter() - commit_started

        count = session.scalar(select(func.count()).select_from(Employee))

    assert preview.invalid_rows == 0
    assert preview_seconds < 30
    assert commit_seconds < 30
    assert summary.created == 3_000
    assert count == 3_020
    engine.dispose()
