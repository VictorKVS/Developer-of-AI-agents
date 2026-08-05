from collections.abc import Sequence

from mongoose_core.ports.llm import LLMMessage, LLMProvider, LLMResult


class DialogueService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def reply(
        self,
        messages: Sequence[LLMMessage],
        *,
        workspace_context: str | None = None,
    ) -> LLMResult:
        system_instruction = (
            "Ты полезный диалоговый AI-ассистент. Отвечай по-русски, "
            "кратко и по существу. Не выдумывай факты."
        )

        if workspace_context:
            system_instruction += (
                "\n\nНиже приведён доверенный контекст текущего рабочего пространства. "
                "Используй его при ответах о кандидате, резюме, навыках, опыте, "
                "карьерных целях и результатах анализа. Не утверждай ничего, "
                "чего нет в этом контексте.\n\n"
                f"{workspace_context}"
            )

        return await self._provider.generate(
            messages,
            system_instruction=system_instruction,
        )
