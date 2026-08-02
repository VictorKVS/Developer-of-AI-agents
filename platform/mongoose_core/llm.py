from dataclasses import dataclass
from typing import Protocol, Sequence

from gigachat import GigaChat


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str


class LLMProvider(Protocol):
    async def generate(self, messages: Sequence[LLMMessage]) -> LLMResult:
        ...


class GigaChatProvider:
    def __init__(
        self,
        *,
        credentials: str,
        model: str,
        scope: str,
        verify_ssl_certs: bool,
        ca_bundle_file: str | None,
    ) -> None:
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS is not configured.")
        self._model = model
        self._client = GigaChat(
            credentials=credentials,
            model=model,
            scope=scope,
            verify_ssl_certs=verify_ssl_certs,
            ca_bundle_file=ca_bundle_file,
        )

    async def generate(self, messages: Sequence[LLMMessage]) -> LLMResult:
        transcript = "\n".join(f"{message.role.upper()}: {message.content}" for message in messages)
        prompt = (
            "Ты полезный корпоративный AI-ассистент. Отвечай по-русски, кратко, "
            "точно и не выдумывай факты.\n\n" + transcript
        )
        response = await self._client.achat(prompt)
        text = response.choices[0].message.content.strip()
        if not text:
            raise RuntimeError("GigaChat returned an empty response.")
        return LLMResult(text=text, model=self._model)
