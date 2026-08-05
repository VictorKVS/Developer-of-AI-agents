import io
import json
import logging
import re
from pathlib import Path

from asgiref.sync import async_to_sync
from docx import Document
from pydantic import BaseModel, Field
from pypdf import PdfReader

from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider

logger = logging.getLogger("apps.web.career")

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}
TARGET_ROLES = {
    "ai_agent_developer": "AI Agent Developer",
    "security_architect": "Архитектор информационной безопасности",
}
DEFAULT_DISCLAIMER = (
    "Оценка основана только на содержании загруженного резюме "
    "и не является гарантией трудоустройства."
)

SENSITIVE_CAREER_REPLACEMENTS = (
    (r"(?i)военн(?:ая|ой|ую|ые|ый|ого)?\s+служб\w*", "государственная служба"),
    (r"(?i)военнослужащ\w*", "государственный специалист"),
    (r"(?i)антитеррористическ\w*", "комплексная объектовая безопасность"),
    (r"(?i)террористическ\w*", "угрозы объектовой безопасности"),
    (r"(?i)экстремистск\w*", "риски общественной безопасности"),
    (r"(?i)противодейств\w*\s+техническ\w*\s+средств\w*\s+разведк\w*", "защита от внешних технических угроз"),
    (r"(?i)разведк\w*", "внешних угроз"),
    (r"(?i)секретн\w*", "ограниченного доступа"),
    (r"(?i)государственн\w*\s+тайн\w*", "информации ограниченного доступа"),
    (r"(?i)оружи\w*", "специализированных средств"),
)


class TrackStep(BaseModel):
    order: int
    title: str
    purpose: str
    deliverable: str


class CareerTrackResult(BaseModel):
    target_role: str
    profile_summary: str
    strengths: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    critical_gaps: list[str] = Field(default_factory=list)
    recommended_projects: list[str] = Field(default_factory=list)
    track: list[TrackStep] = Field(default_factory=list)
    readiness_percent: int = Field(ge=0, le=100)
    next_checkpoint: str
    missing_information: list[str] = Field(default_factory=list)
    disclaimer: str = DEFAULT_DISCLAIMER


def extract_resume_text(uploaded_file) -> str:
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError("Файл превышает допустимый размер 5 МБ.")

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Разрешены только PDF, DOCX и TXT.")

    raw = uploaded_file.read()
    if suffix == ".txt":
        text = raw.decode("utf-8-sig", errors="replace")
    elif suffix == ".pdf":
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        document = Document(io.BytesIO(raw))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) < 120:
        raise ValueError("Не удалось извлечь достаточно текста из резюме.")
    return normalized[:30000]


def _prepare_resume_for_career_analysis(resume_text: str) -> str:
    """Build a career-only copy without changing the Workspace source document."""
    prepared = resume_text
    for pattern, replacement in SENSITIVE_CAREER_REPLACEMENTS:
        prepared = re.sub(pattern, replacement, prepared)

    prepared = re.sub(r"\s+", " ", prepared).strip()
    return prepared[:20000]


def _extract_json(text: str) -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("AI-модель вернула пустой ответ вместо структурированного анализа.")

    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        preview = cleaned[:300].replace("\n", " ")
        raise ValueError(
            "AI-модель вернула ответ без JSON-объекта. "
            f"Начало ответа: {preview}"
        )

    candidate = cleaned[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Career JSON parse failed line=%s column=%s preview=%r",
            exc.lineno,
            exc.colno,
            candidate[:500],
        )
        raise ValueError(
            "AI-модель вернула повреждённый JSON. "
            f"Ошибка в строке {exc.lineno}, позиция {exc.colno}."
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError("Структурированный ответ AI должен быть JSON-объектом.")
    return payload


def _item_to_text(item) -> str:
    """Convert a flexible LLM list item into readable plain text."""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        preferred_keys = (
            "title",
            "name",
            "skill",
            "project",
            "description",
            "reason",
            "value",
        )
        parts = []
        for key in preferred_keys:
            value = item.get(key)
            if value and str(value).strip() not in parts:
                parts.append(str(value).strip())
        if not parts:
            parts = [str(value).strip() for value in item.values() if value]
        return " — ".join(parts)
    return str(item).strip()


def _normalize_text_list(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    return [text for item in value if (text := _item_to_text(item))]


def _normalize_track(value) -> list[dict]:
    if not isinstance(value, list):
        return []

    normalized = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            normalized.append(
                {
                    "order": index,
                    "title": item,
                    "purpose": "Выполнить этап персонального трека развития.",
                    "deliverable": "Подтверждённый результат этапа.",
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        normalized.append(
            {
                "order": item.get("order") or index,
                "title": item.get("title") or item.get("name") or f"Этап {index}",
                "purpose": item.get("purpose") or item.get("reason") or item.get("description") or "Развить требуемую компетенцию.",
                "deliverable": item.get("deliverable") or item.get("result") or item.get("outcome") or "Проверяемый результат этапа.",
            }
        )
    return normalized


def _normalize_career_payload(payload: dict, target_role: str) -> dict:
    payload = dict(payload or {})
    payload["target_role"] = payload.get("target_role") or target_role
    payload["profile_summary"] = payload.get("profile_summary") or payload.get("summary") or "Профиль сформирован по загруженному резюме."

    for field_name in (
        "strengths",
        "transferable_skills",
        "critical_gaps",
        "recommended_projects",
        "missing_information",
    ):
        payload[field_name] = _normalize_text_list(payload.get(field_name))

    payload["track"] = _normalize_track(payload.get("track"))
    payload["readiness_percent"] = payload.get("readiness_percent", 0)
    payload["next_checkpoint"] = payload.get("next_checkpoint") or "Завершить первый этап трека и подтвердить результат артефактом."
    payload["disclaimer"] = payload.get("disclaimer") or DEFAULT_DISCLAIMER
    return payload


def _career_system_prompt(target_role: str) -> str:
    return f"""
Ты Career Track Analyst платформы MONGOOSE AI.
Это синтетическое демонстрационное резюме. Выполняй только профессиональный анализ компетенций и карьерного соответствия целевой роли: {target_role}.
Не оценивай политические взгляды, благонадёжность, здоровье, личную жизнь и иные чувствительные характеристики. Не делай проверку службы безопасности.
Учитывай только опыт, навыки, проекты, образование и профессиональные результаты. Не выдумывай отсутствующие факты.
Верни только валидный JSON без Markdown и без пояснений до или после JSON:
{{
  "target_role": "{target_role}",
  "profile_summary": "...",
  "strengths": ["..."],
  "transferable_skills": ["..."],
  "critical_gaps": ["..."],
  "recommended_projects": ["..."],
  "track": [
    {{"order": 1, "title": "...", "purpose": "...", "deliverable": "..."}}
  ],
  "readiness_percent": 0,
  "next_checkpoint": "...",
  "missing_information": ["..."],
  "disclaimer": "{DEFAULT_DISCLAIMER}"
}}
Все элементы strengths, transferable_skills, critical_gaps, recommended_projects и missing_information должны быть строками, не объектами.
Сделай практический трек из 5-7 последовательных шагов. Для каждого шага укажи проверяемый результат.
""".strip()


def build_career_track(resume_text: str, target_role_key: str) -> tuple[CareerTrackResult, str]:
    target_role = TARGET_ROLES.get(target_role_key)
    if not target_role:
        raise ValueError("Неизвестная целевая роль.")

    analysis_resume = _prepare_resume_for_career_analysis(resume_text)
    system_prompt = _career_system_prompt(target_role)
    provider = build_llm_provider()
    result = async_to_sync(provider.generate)(
        [LLMMessage(role="user", content=analysis_resume)],
        system_instruction=system_prompt,
    )

    try:
        payload = _extract_json(result.text)
    except ValueError as first_error:
        logger.warning(
            "Career analysis response requires repair model=%s error=%s preview=%r",
            result.model,
            first_error,
            (result.text or "")[:500],
        )
        repair_prompt = (
            "Повтори профессиональный анализ этого синтетического резюме. "
            "Учитывай только опыт, навыки, проекты и образование. "
            "Верни только один валидный JSON-объект строго по заданной схеме, "
            "без Markdown, комментариев и вводного текста."
        )
        retry_provider = build_llm_provider()
        repaired = async_to_sync(retry_provider.generate)(
            [LLMMessage(role="user", content=analysis_resume + "\n\n" + repair_prompt)],
            system_instruction=system_prompt,
        )
        payload = _extract_json(repaired.text)
        result = repaired

    normalized = _normalize_career_payload(payload, target_role)
    parsed = CareerTrackResult.model_validate(normalized)
    return parsed, result.model
