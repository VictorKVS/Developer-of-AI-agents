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
    disclaimer: str


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
  "strengths": [],
  "transferable_skills": [],
  "critical_gaps": [],
  "recommended_projects": [],
  "track": [
    {{"order": 1, "title": "...", "purpose": "...", "deliverable": "..."}}
  ],
  "readiness_percent": 0,
  "next_checkpoint": "...",
  "missing_information": [],
  "disclaimer": "Оценка основана только на содержании загруженного резюме и не является гарантией трудоустройства."
}}
Сделай практический трек из 5-7 последовательных шагов. Для каждого шага укажи проверяемый результат.
""".strip()

    provider = build_llm_provider()
    result = async_to_sync(provider.generate)(
        [LLMMessage(role="user", content=resume_text)],
        system_instruction=system_prompt,
    )
    parsed = CareerTrackResult.model_validate(_extract_json(result.text))
    return parsed, result.model
