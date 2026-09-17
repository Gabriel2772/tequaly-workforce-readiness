from enum import StrEnum


class EligibilityReasonCode(StrEnum):
    INACTIVE_EMPLOYEE = "inactive_employee"
    INCOMPATIBLE_ROLE = "incompatible_role"
    UNAVAILABLE_FOR_OPERATION = "unavailable_for_operation"
    ASSIGNMENT_CONFLICT = "assignment_conflict"
    MISSING_AUTHORIZATION = "missing_authorization"
    AUTHORIZATION_EXPIRES_BEFORE_END = "authorization_expires_before_end"
    MISSING_QUALIFICATION = "missing_qualification"
    TRAINING_AFTER_DEADLINE = "training_after_deadline"
    INSUFFICIENT_EXPERIENCE = "insufficient_experience"
    OPERATIONAL_RESTRICTION = "operational_restriction"
    QUALIFICATION_EXPIRES_BEFORE_END = "qualification_expires_before_end"


REASON_MESSAGES: dict[EligibilityReasonCode, str] = {
    EligibilityReasonCode.INACTIVE_EMPLOYEE: "Colaborador inativo.",
    EligibilityReasonCode.INCOMPATIBLE_ROLE: "Cargo ou fun��o incompat�vel com a demanda.",
    EligibilityReasonCode.UNAVAILABLE_FOR_OPERATION: "Disponibilidade n�o cobre a opera��o.",
    EligibilityReasonCode.ASSIGNMENT_CONFLICT: "Existe uma aloca��o conflitante no per�odo.",
    EligibilityReasonCode.MISSING_AUTHORIZATION: "Autoriza��o obrigat�ria ausente.",
    EligibilityReasonCode.AUTHORIZATION_EXPIRES_BEFORE_END: (
        "Autoriza��o expira antes do fim da opera��o."
    ),
    EligibilityReasonCode.MISSING_QUALIFICATION: "Qualifica��o obrigat�ria ausente.",
    EligibilityReasonCode.TRAINING_AFTER_DEADLINE: (
        "Capacita��o termina ap�s o prazo de mobiliza��o."
    ),
    EligibilityReasonCode.INSUFFICIENT_EXPERIENCE: "Experi�ncia abaixo do m�nimo exigido.",
    EligibilityReasonCode.OPERATIONAL_RESTRICTION: "Restri��o operacional aplic�vel.",
    EligibilityReasonCode.QUALIFICATION_EXPIRES_BEFORE_END: (
        "Qualifica��o expira antes do fim da opera��o."
    ),
}
