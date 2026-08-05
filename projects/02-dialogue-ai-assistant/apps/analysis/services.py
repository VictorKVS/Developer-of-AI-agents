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
Поле profile.experience всегда возвращай одной строкой, а не списком или объектом.
""".strip()


def _extract_json(text: str) -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Аналитическая модель вернула пустой ответ.")

    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Аналитическая модель не вернула JSON-объект.")
    return json.loads(cleaned[start : end + 1])


def _item_to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = ("title", "name", "value", "description", "reason", "next_step")
        parts = [str(value[key]).strip() for key in preferred if value.get(key)]
        if not parts:
            parts = [str(item).strip() for item in value.values() if item]
        return " — ".join(dict.fromkeys(parts))
    if isinstance(value, list):
        return "; ".join(filter(None, (_item_to_text(item) for item in value)))
    return str(value).strip()


def _to_text_list(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    result = []
    for item in value:
        text = _item_to_text(item)
        if text:
            result.append(text)
    return result


def _normalize_recommendations(value) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]

    normalized = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            normalized.append(
                {
                    "title": f"Рекомендация {index}",
                    "reason": item,
                    "next_step": "Уточнить и выполнить следующий практический шаг.",
                }
            )
            continue
        if isinstance(item, dict):
            normalized.append(
                {
                    "title": _item_to_text(item.get("title") or item.get("name")) or f"Рекомендация {index}",
                    "reason": _item_to_text(item.get("reason") or item.get("description")) or "Основано на анализе диалога.",
                    "next_step": _item_to_text(item.get("next_step") or item.get("action") or item.get("step")) or "Сформировать проверяемый следующий шаг.",
                }
            )
    return normalized


def _normalize_analysis_payload(payload: dict) -> dict:
    payload = dict(payload or {})
    profile = dict(payload.get("profile") or {})

    profile["name"] = _item_to_text(profile.get("name")) or None
    profile["goals"] = _to_text_list(profile.get("goals"))
    profile["experience"] = _item_to_text(profile.get("experience"))
    profile["interests"] = _to_text_list(profile.get("interests"))
    profile["constraints"] = _to_text_list(profile.get("constraints"))

    payload["profile"] = profile
    payload["summary"] = _item_to_text(payload.get("summary")) or "Аналитическое резюме сформировано по истории диалога."
    payload["recommendations"] = _normalize_recommendations(payload.get("recommendations"))
    payload["missing_information"] = _to_text_list(payload.get("missing_information"))
    payload["disclaimer"] = _item_to_text(payload.get("disclaimer")) or "Результат требует проверки человеком."

    confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence > 1:
        confidence = confidence / 100
    payload["confidence"] = max(0.0, min(1.0, confidence))
    return payload


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
    payload = _normalize_analysis_payload(_extract_json(result.text))
    parsed = AnalysisResult.model_validate(payload)
    parsed.disclaimer = profile.disclaimer
    return parsed, result.model, profile
