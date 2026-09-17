from collections.abc import Callable
from datetime import date, timedelta
from uuid import UUID

from app.workforce.repository import ProfileRepository
from app.workforce.schemas import (
    AssignmentSummary,
    AuthorizationSummary,
    AvailabilitySummary,
    CostSummary,
    EmployeeProfileVector,
    QualificationSummary,
    RestrictionSummary,
    TechnicalCompetencySummary,
    TrainingSummary,
)


def qualification_status(
    issued_on: date,
    expires_on: date | None,
    reference_date: date,
    *,
    expiring_window_days: int = 30,
) -> str:
    if issued_on > reference_date:
        return "futura"
    if expires_on is None:
        return "válida"
    if expires_on < reference_date:
        return "vencida"
    if expires_on <= reference_date + timedelta(days=expiring_window_days):
        return "vence_em_breve"
    return "válida"


class EmployeeNotFoundError(LookupError):
    pass


class EmployeeProfileService:
    def __init__(
        self,
        repository: ProfileRepository,
        *,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._today = today

    def get_profile(self, employee_id: UUID) -> EmployeeProfileVector:
        source = self._repository.get_profile_source(employee_id)
        if source is None:
            raise EmployeeNotFoundError(str(employee_id))

        reference_date = self._today()
        return EmployeeProfileVector(
            cargo_funcao_principal=source.role_name,
            nome=source.name,
            qualificacoes=[
                QualificationSummary(
                    id=qualification.id,
                    nome=qualification.name,
                    categoria=qualification.category,
                    emitida_em=qualification.issued_on,
                    vence_em=qualification.expires_on,
                    status=qualification_status(
                        qualification.issued_on,
                        qualification.expires_on,
                        reference_date,
                    ),
                )
                for qualification in source.qualifications
            ],
            competencias_tecnicas=[
                TechnicalCompetencySummary(
                    nome=competency.name,
                    nivel=competency.level,
                    avaliada_em=competency.assessed_on,
                )
                for competency in source.competencies
            ],
            autorizacoes=[
                AuthorizationSummary(
                    nome=authorization.name,
                    escopo=authorization.scope,
                    vence_em=authorization.expires_on,
                    status=qualification_status(
                        authorization.issued_on,
                        authorization.expires_on,
                        reference_date,
                    ),
                )
                for authorization in source.authorizations
            ],
            disponibilidade=[
                AvailabilitySummary(
                    inicio=availability.starts_at,
                    fim=availability.ends_at,
                    status=availability.status,
                )
                for availability in source.availability
            ],
            base_localizacao=source.base_location,
            experiencia_senioridade=source.seniority_level,
            alocacoes=[
                AssignmentSummary(
                    operacao=assignment.operation_name,
                    inicio=assignment.starts_at,
                    fim=assignment.ends_at,
                    status=assignment.status,
                )
                for assignment in source.assignments
            ],
            custos_incrementais=[
                CostSummary(
                    moeda=cost.currency,
                    custo_hora_centavos=cost.hourly_cost_cents,
                    custo_viagem_centavos=cost.travel_cost_cents,
                    vigencia_inicio=cost.effective_from,
                )
                for cost in source.costs
            ],
            capacitacoes_agendadas=[
                TrainingSummary(
                    treinamento=training.training_name,
                    inicio=training.starts_at,
                    fim=training.ends_at,
                    status=training.status,
                )
                for training in source.training
            ],
            restricoes_operacionais=[
                RestrictionSummary(
                    restricao=restriction.restriction_name,
                    escopo=restriction.scope,
                    inicio=restriction.starts_at,
                    fim=restriction.ends_at,
                )
                for restriction in source.restrictions
            ],
            prontidao={"status": "não_avaliada"},
            updated_at=source.updated_at,
        )
