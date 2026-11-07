"""Select the accepted chat-API mode or the bounded tool-loop fallback."""

from collections.abc import AsyncIterator

from .chat_api import ChatAPIClient
from .models import AnswerResult, ConnectorError
from .settings import Settings
from .tool_loop import ToolLoop

STREAM_CHUNK_SIZE = 64


class KnowledgeGraphConnector:
    """Coordinate the configured answer path and stream the completed answer."""

    def __init__(
        self,
        settings: Settings,
        chat_api: ChatAPIClient | None = None,
        tool_loop: ToolLoop | None = None,
    ) -> None:
        self.settings = settings
        self.chat_api = chat_api or ChatAPIClient(settings)
        self.tool_loop = tool_loop or ToolLoop(settings)

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

    async def stream(self, question: str) -> AsyncIterator[str]:
        result = await self.answer(question)
        for index in range(0, len(result.text), STREAM_CHUNK_SIZE):
            yield result.text[index : index + STREAM_CHUNK_SIZE]
