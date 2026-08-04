import json
import re

from asgiref.sync import async_to_sync

from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider

from .schemas import AnalysisResult


ANALYSIS_SYSTEM_PROMPT = """
Ты вторая аналитическая модель MONGOOSE AI PLATFORM.
Проанализируй ВСЮ историю диалога, а не отдельные поля.
Верни только валидный JSON без Markdown по схеме:
{
  "profile": {
    "name": null,
    "goals": [],
    "experience": "",
    "interests": [],
    "constraints": []
  },
  "summary": "содержательное резюме диалога",
  "recommendations": [
    {"title": "...", "reason": "...", "next_step": "..."}
  ],
  "confidence": 0.0,
  "missing_information": [],
  "disclaimer": "Выводы основаны только на информации из диалога."
}
Не выдумывай факты. Не делай медицинских, юридических или финансовых утверждений,
которых нет в диалоге. Если данных мало, прямо укажи это.
""".strip()


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def analyze_conversation(conversation):
    history = [
        LLMMessage(role=item.role, content=item.content)
        for item in conversation.messages.order_by("sequence_number")
    ]
    if not history:
        raise ValueError("Диалог пуст. Сначала добавьте сообщения.")

    provider = build_llm_provider()
    result = async_to_sync(provider.generate)(
        history,
        system_instruction=ANALYSIS_SYSTEM_PROMPT,
    )
    parsed = AnalysisResult.model_validate(_extract_json(result.text))
    return parsed, result.model
