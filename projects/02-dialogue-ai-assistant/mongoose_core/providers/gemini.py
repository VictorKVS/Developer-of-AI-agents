from collections.abc import Sequence

from google import genai
from google.genai import types

from mongoose_core.ports.llm import LLMMessage, LLMResult


class GeminiProvider:
    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        *,
        system_instruction: str | None = None,
    ) -> LLMResult:
        transcript = "\n".join(
            f"{message.role.upper()}: {message.content}" for message in messages
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=transcript,
            config=config,
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return LLMResult(text=text, model=self._model)
