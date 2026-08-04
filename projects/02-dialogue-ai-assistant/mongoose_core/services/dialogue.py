from collections.abc import Sequence

from mongoose_core.ports.llm import LLMMessage, LLMProvider, LLMResult


class DialogueService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def reply(self, messages: Sequence[LLMMessage]) -> LLMResult:
        return await self._provider.generate(
            messages,
            system_instruction=(
                "Ты полезный диалоговый AI-ассистент. Отвечай по-русски, "
                "кратко и по существу. Не выдумывай факты."
            ),
        )
