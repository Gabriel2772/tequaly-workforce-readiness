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
    EligibilityReasonCode.INCOMPATIBLE_ROLE: "Cargo ou função incompatível com a demanda.",
    EligibilityReasonCode.UNAVAILABLE_FOR_OPERATION: "Disponibilidade não cobre a operação.",
    EligibilityReasonCode.ASSIGNMENT_CONFLICT: "Existe uma alocação conflitante no período.",
    EligibilityReasonCode.MISSING_AUTHORIZATION: "Autorização obrigatória ausente.",
    EligibilityReasonCode.AUTHORIZATION_EXPIRES_BEFORE_END: (
        "Autorização expira antes do fim da operação."
    ),
    EligibilityReasonCode.MISSING_QUALIFICATION: "Qualificação obrigatória ausente.",
    EligibilityReasonCode.TRAINING_AFTER_DEADLINE: (
        "Capacitação termina após o prazo de mobilização."
    ),
    EligibilityReasonCode.INSUFFICIENT_EXPERIENCE: "Experiência abaixo do mínimo exigido.",
    EligibilityReasonCode.OPERATIONAL_RESTRICTION: "Restrição operacional aplicável.",
    EligibilityReasonCode.QUALIFICATION_EXPIRES_BEFORE_END: (
        "Qualificação expira antes do fim da operação."
    ),
}
