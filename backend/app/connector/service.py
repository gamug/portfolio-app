"""Select the accepted chat-API mode or the bounded tool-loop fallback."""

from collections.abc import AsyncIterator

from .chat_api import ChatAPIClient
from .models import AnswerResult, ChatAnswer, ConnectorError
from .openui import OpenUIConverter
from .settings import Settings
from .storage import InMemoryQuestionAnswerStore, QuestionAnswerPair, QuestionAnswerStore
from .tool_loop import ToolLoop

STREAM_CHUNK_SIZE = 64
DEFAULT_SESSION_ID = "default"


class KnowledgeGraphConnector:
    """Coordinate the configured answer path and stream the completed answer."""

    def __init__(
        self,
        settings: Settings,
        chat_api: ChatAPIClient | None = None,
        tool_loop: ToolLoop | None = None,
        converter: OpenUIConverter | None = None,
        store: QuestionAnswerStore | None = None,
    ) -> None:
        self.settings = settings
        self.chat_api = chat_api or ChatAPIClient(settings)
        self.tool_loop = tool_loop or ToolLoop(settings)
        self.converter = converter or OpenUIConverter(settings)
        self.store = store or InMemoryQuestionAnswerStore()

    async def check_startup(self) -> None:
        await self.chat_api.check_startup()
        if self.settings.chat_mode == "tool_loop":
            await self.tool_loop.check_startup()

    async def answer(self, question: str) -> AnswerResult:
        if not question.strip():
            raise ConnectorError("The question is empty.", status_code=400)
        if self.settings.chat_mode == "tool_loop":
            return await self.tool_loop.answer(question)
        return await self.chat_api.answer(question)

    async def answer_and_store(
        self, question: str, session_id: str = DEFAULT_SESSION_ID
    ) -> ChatAnswer:
        """Convert only after the answer completes, then store the completed pair."""
        result = await self.answer(question)
        conversion = await self.converter.convert(result.text)
        pair = QuestionAnswerPair(
            session_id=session_id or DEFAULT_SESSION_ID,
            question=question,
            raw_answer=result.text,
            openui_lang=conversion.text,
            relevant=True,
        )
        await self.store.save(pair)
        return ChatAnswer(raw=result, conversion=conversion)

    async def stream(self, question: str) -> AsyncIterator[str]:
        result = await self.answer_and_store(question)
        for index in range(0, len(result.raw.text), STREAM_CHUNK_SIZE):
            yield result.raw.text[index : index + STREAM_CHUNK_SIZE]
