import asyncio

from app.connector.storage import InMemoryQuestionAnswerStore, QuestionAnswerPair


def test_in_memory_store_keeps_pairs_by_session() -> None:
    store = InMemoryQuestionAnswerStore()
    first = QuestionAnswerPair(
        session_id="s1",
        question="q1",
        raw_answer="a1",
        openui_lang="root = Card([])",
    )
    second = QuestionAnswerPair(
        session_id="s2",
        question="q2",
        raw_answer="a2",
        openui_lang="root = Card([])",
    )
    asyncio.run(store.save(first))
    asyncio.run(store.save(second))
    assert asyncio.run(store.list_for_session("s1")) == [first]
    assert asyncio.run(store.list_for_session("s2")) == [second]
    assert first.relevant is True
