import json
import re

from asgiref.sync import async_to_sync

from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider

from .profiles import get_analysis_profile
from .schemas import AnalysisResult


BASE_ANALYSIS_PROMPT = """
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
  "summary": "содержательное резюме диалога в выбранной аналитической перспективе",
  "recommendations": [
    {"title": "...", "reason": "...", "next_step": "..."}
  ],
  "confidence": 0.0,
  "missing_information": [],
  "disclaimer": "..."
}
Не выдумывай факты. Отделяй наблюдения от гипотез. Если данных мало, прямо укажи это.
Не делай медицинских, юридических или финансовых утверждений, которых нет в диалоге.
""".strip()


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def analyze_conversation(conversation, profile_key: str | None = None):
    history = [
        LLMMessage(role=item.role, content=item.content)
        for item in conversation.messages.order_by("sequence_number")
    ]
    if not history:
        raise ValueError("Диалог пуст. Сначала добавьте сообщения.")

    profile = get_analysis_profile(profile_key)
    system_instruction = (
        f"{BASE_ANALYSIS_PROMPT}\n\n"
        f"ВЫБРАННЫЙ ПРОФИЛЬ: {profile.title}.\n"
        f"ИНСТРУКЦИЯ ПРОФИЛЯ: {profile.system_prompt}\n"
        f"ОБЯЗАТЕЛЬНЫЙ ДИСКЛЕЙМЕР: {profile.disclaimer}"
    )

    provider = build_llm_provider()
    result = async_to_sync(provider.generate)(
        history,
        system_instruction=system_instruction,
    )
    parsed = AnalysisResult.model_validate(_extract_json(result.text))
    parsed.disclaimer = profile.disclaimer
    return parsed, result.model, profile
