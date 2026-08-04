import io
import json
import re
from pathlib import Path

from asgiref.sync import async_to_sync
from docx import Document
from pydantic import BaseModel, Field
from pypdf import PdfReader

from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider

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


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


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


def build_career_track(resume_text: str, target_role_key: str) -> tuple[CareerTrackResult, str]:
    target_role = TARGET_ROLES.get(target_role_key)
    if not target_role:
        raise ValueError("Неизвестная целевая роль.")

    system_prompt = f"""
Ты Career Track Analyst платформы MONGOOSE AI.
Проанализируй резюме только по имеющимся фактам и сопоставь его с целевой ролью: {target_role}.
Не выдумывай опыт, достижения и навыки. Верни только валидный JSON без Markdown:
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

    provider = build_llm_provider()
    result = async_to_sync(provider.generate)(
        [LLMMessage(role="user", content=resume_text)],
        system_instruction=system_prompt,
    )
    payload = _normalize_career_payload(_extract_json(result.text), target_role)
    parsed = CareerTrackResult.model_validate(payload)
    return parsed, result.model
