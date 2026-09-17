from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from app.workforce.repository import EmployeeProfileSource, QualificationSource
from app.workforce.schemas import EmployeeProfileVector


def test_profile_vector_starts_with_required_fields() -> None:
    profile = EmployeeProfileVector(
        cargo_funcao_principal="Soldador",
        nome="Colaborador Sintético 00001",
        qualificacoes=[],
        competencias_tecnicas=[],
        autorizacoes=[],
        disponibilidade=[],
        base_localizacao="Curitiba",
        experiencia_senioridade="pleno",
        alocacoes=[],
        custos_incrementais=[],
        capacitacoes_agendadas=[],
        restricoes_operacionais=[],
        prontidao={"status": "não_avaliada"},
        updated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    keys = list(profile.model_dump().keys())
    assert keys[:3] == ["cargo_funcao_principal", "nome", "qualificacoes"]
    assert keys == [
        "cargo_funcao_principal",
        "nome",
        "qualificacoes",
        "competencias_tecnicas",
        "autorizacoes",
        "disponibilidade",
        "base_localizacao",
        "experiencia_senioridade",
        "alocacoes",
        "custos_incrementais",
        "capacitacoes_agendadas",
        "restricoes_operacionais",
        "prontidao",
        "updated_at",
    ]


def test_qualification_status_is_not_accepted_as_a_stored_field() -> None:
    from app.workforce.profile_service import qualification_status

    reference = date(2026, 8, 10)

    assert qualification_status(date(2025, 1, 1), date(2026, 8, 9), reference) == "vencida"
    assert qualification_status(date(2025, 1, 1), date(2026, 8, 25), reference) == "vence_em_breve"
    assert qualification_status(date(2026, 9, 1), date(2028, 9, 1), reference) == "futura"
    assert qualification_status(date(2025, 1, 1), None, reference) == "válida"


class FakeProfileRepository:
    def __init__(self, source: EmployeeProfileSource | None) -> None:
        self.source = source

    def get_profile_source(self, _employee_id: UUID) -> EmployeeProfileSource | None:
        return self.source


def test_profile_service_derives_qualification_statuses() -> None:
    from app.workforce.profile_service import EmployeeProfileService

    source = EmployeeProfileSource(
        role_name="Soldador",
        name="Colaborador Sintético 00001",
        base_location="Curitiba",
        seniority_level="pleno",
        updated_at=datetime(2026, 8, 10, tzinfo=UTC),
        qualifications=(
            QualificationSource(
                id=UUID("1c359b98-4ae9-4f77-a984-a30de9f5b4a4"),
                name="NR-35",
                category="segurança",
                issued_on=date(2025, 8, 1),
                expires_on=date(2026, 8, 20),
            ),
        ),
    )
    service = EmployeeProfileService(
        FakeProfileRepository(source),
        today=lambda: date(2026, 8, 10),
    )

    profile = service.get_profile(UUID("cdfed211-0abb-4930-a7ab-a91214dcde11"))

    assert profile.qualificacoes[0].status == "vence_em_breve"
    assert profile.prontidao == {"status": "não_avaliada"}


def test_profile_service_rejects_unknown_employee() -> None:
    from app.workforce.profile_service import EmployeeNotFoundError, EmployeeProfileService

    service = EmployeeProfileService(FakeProfileRepository(None))

    with pytest.raises(EmployeeNotFoundError):
        service.get_profile(UUID("cdfed211-0abb-4930-a7ab-a91214dcde11"))
