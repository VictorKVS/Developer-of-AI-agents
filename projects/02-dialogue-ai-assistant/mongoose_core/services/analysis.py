import json
import re
from collections.abc import Sequence

from pydantic import ValidationError

from mongoose_core.ports.llm import LLMMessage, LLMProvider
from mongoose_core.prompts.analysis import ANALYSIS_SYSTEM_PROMPT
from mongoose_core.schemas.analysis import AnalysisPayload, AnalysisResult


class AnalysisServiceError(RuntimeError):
    """Raised when the analytical model returns an unusable result."""


class AnalysisService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def analyze(self, messages: Sequence[LLMMessage]) -> AnalysisResult:
        if not messages:
            raise ValueError("Conversation history is empty.")

        result = await self._provider.generate(
            messages,
            system_instruction=ANALYSIS_SYSTEM_PROMPT,
        )
        payload = self._parse_payload(result.text)
        return AnalysisResult(**payload.model_dump(), model=result.model)

    @staticmethod
    def _parse_payload(raw_text: str) -> AnalysisPayload:
        cleaned = raw_text.strip()
        fenced = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            cleaned = fenced.group(1).strip()

        try:
            data = json.loads(cleaned)
            return AnalysisPayload.model_validate(data)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise AnalysisServiceError(
                "The analytical model returned invalid structured data."
            ) from exc
