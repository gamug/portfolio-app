"""User-safe report messages and prompt instructions in the analyst's language."""

from app.connector.language import Language

REPORT_MESSAGES: dict[Language, dict[str, str]] = {
    "en": {
        "not_found": "The session was not found.",
        "no_history": "This session has no history. Start the data exploration first.",
        "no_relevant": (
            "No question-answer pair is marked as relevant. Mark at least one pair first."
        ),
        "generation": "The report could not be generated. Please try again.",
        "partial": (
            "The report could not be generated. The partial report was saved as incomplete."
        ),
        "storage": "The report could not be saved. Please try again.",
        "unavailable": "The report agent is not available. Please try again.",
    },
    "es": {
        "not_found": "No se encontró la sesión.",
        "no_history": ("Esta sesión no tiene historial. Empieza primero la exploración de datos."),
        "no_relevant": (
            "Ningún par de pregunta y respuesta está marcado como relevante. "
            "Marca al menos un par primero."
        ),
        "generation": "No se pudo generar el informe. Inténtalo de nuevo.",
        "partial": ("No se pudo generar el informe. El informe parcial se guardó como incompleto."),
        "storage": "No se pudo guardar el informe. Inténtalo de nuevo.",
        "unavailable": "El agente de informes no está disponible. Inténtalo de nuevo.",
    },
}


def report_error_message(kind: str, language: Language, *, partial: bool = False) -> str:
    """Return a user-safe message; internal error details never reach the client."""
    messages = REPORT_MESSAGES[language]
    if kind == "generation" and partial:
        return messages["partial"]
    return messages.get(kind, messages["generation"])


def plan_language_instruction(language: Language) -> str:
    if language == "es":
        return (
            "Escribe el título, el resumen, los títulos de los gráficos, las conclusiones "
            "de cada gráfico y las conclusiones finales en español. No cambies los nombres "
            "propios, las etiquetas ni las cifras."
        )
    return (
        "Write the title, the summary, the chart titles, each chart takeaway and the "
        "closing conclusions in English. Do not change proper names, labels or figures."
    )


def render_language_instruction(language: Language) -> str:
    if language == "es":
        return (
            "El plan ya está en español. Conserva todo el texto visible exactamente como "
            "aparece en el plan; no lo traduzcas ni lo reescribas."
        )
    return (
        "The plan is already in English. Keep every visible string exactly as it appears "
        "in the plan; do not translate or rewrite it."
    )
