from app.connector.language import (
    answer_instruction,
    conversion_instruction,
    detect_language,
    error_message,
)


def test_detects_spanish_question() -> None:
    assert detect_language("¿Cuál fue el resultado del último mes?") == "es"
    assert detect_language("¿Qué datos contiene el grafo?") == "es"


def test_defaults_to_english() -> None:
    assert detect_language("What was the result of the last month?") == "en"


def test_instructions_follow_the_language() -> None:
    assert "español" in answer_instruction("es")
    assert "English" in answer_instruction("en")
    assert "español" in conversion_instruction("es")
    assert "English" in conversion_instruction("en")


def test_error_messages_are_localized_and_generic() -> None:
    assert "grafo" in error_message("graphdb", "es")
    assert "knowledge graph" in error_message("graphdb", "en")
    assert "secreto" not in error_message("deepseek", "es")
