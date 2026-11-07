"""Minimal language handling for the analyst's question and backend errors."""

import re
from typing import Literal

from .models import ErrorKind

Language = Literal["en", "es"]

SPANISH_MARKERS = {
    "que",
    "qué",
    "cual",
    "cuál",
    "como",
    "cómo",
    "cuando",
    "cuándo",
    "donde",
    "dónde",
    "cuanto",
    "cuánto",
    "cuantos",
    "cuántos",
    "por",
    "para",
    "los",
    "las",
    "una",
    "del",
    "es",
    "son",
    "fue",
    "mes",
    "meses",
    "durante",
    "entre",
    "con",
    "sin",
    "más",
    "menos",
    "gracias",
}
SPANISH_CHARACTERS = "áéíóúñü¿¡"

ERROR_MESSAGES: dict[Language, dict[ErrorKind, str]] = {
    "es": {
        "validation": "La pregunta no es válida.",
        "timeout": "La consulta tardó demasiado. Inténtalo de nuevo.",
        "graphdb": "No se pudo consultar el grafo. Inténtalo de nuevo.",
        "deepseek": "No se pudo generar la respuesta. Inténtalo de nuevo.",
        "conversion": "No se pudo preparar la respuesta. Inténtalo de nuevo.",
        "storage": "No se pudo guardar la respuesta. Inténtalo de nuevo.",
        "unknown": "Se produjo un error inesperado. Inténtalo de nuevo.",
    },
    "en": {
        "validation": "The question is not valid.",
        "timeout": "The question took too long. Please try again.",
        "graphdb": "The knowledge graph could not be queried. Please try again.",
        "deepseek": "The answer could not be generated. Please try again.",
        "conversion": "The answer could not be prepared. Please try again.",
        "storage": "The answer could not be saved. Please try again.",
        "unknown": "An unexpected error occurred. Please try again.",
    },
}


def detect_language(text: str) -> Language:
    """Use a small heuristic; the project deliberately has no i18n framework."""
    lowered = text.casefold()
    if any(character in lowered for character in SPANISH_CHARACTERS):
        return "es"
    words = set(re.findall(r"[a-záéíóúñü]+", lowered))
    return "es" if words & SPANISH_MARKERS else "en"


def answer_instruction(language: Language) -> str:
    if language == "es":
        return (
            "Responde en español, el idioma de la pregunta. No cambies los nombres "
            "propios, las etiquetas ni las cifras."
        )
    return (
        "Answer in English, the language of the question. Do not change proper names, "
        "labels or figures."
    )


def conversion_instruction(language: Language) -> str:
    if language == "es":
        return (
            "Escribe todo el texto visible para el usuario en español, el idioma de la "
            "pregunta. Conserva las cifras y los nombres propios."
        )
    return (
        "Write all user-facing text in English, the language of the question. Keep the "
        "figures and proper names unchanged."
    )


def error_message(kind: ErrorKind, language: Language) -> str:
    return ERROR_MESSAGES[language].get(kind, ERROR_MESSAGES[language]["unknown"])
