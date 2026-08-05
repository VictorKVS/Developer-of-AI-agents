import logging
from collections.abc import Sequence

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from pydantic import ValidationError

from mongoose_core.ports.llm import LLMMessage, LLMResult


logger = logging.getLogger("mongoose.providers.gigachat")


class GigaChatProvider:
    def __init__(
        self,
        *,
        credentials: str,
        model: str,
        scope: str = "GIGACHAT_API_PERS",
        verify_ssl_certs: bool = True,
        ca_bundle_file: str | None = None,
    ) -> None:
        if not credentials:
            raise ValueError("GIGACHAT_CREDENTIALS is not configured.")

        self._credentials = credentials
        self._model = model
        self._scope = scope
        self._verify_ssl_certs = verify_ssl_certs
        self._ca_bundle_file = ca_bundle_file
        self._client = self._build_client()

    def _build_client(self) -> GigaChat:
        return GigaChat(
            credentials=self._credentials,
            scope=self._scope,
            model=self._model,
            verify_ssl_certs=self._verify_ssl_certs,
            ca_bundle_file=self._ca_bundle_file or None,
            max_retries=2,
            retry_backoff_factor=0.5,
        )

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        *,
        system_instruction: str | None = None,
    ) -> LLMResult:
        chat_messages: list[Messages] = []

        if system_instruction:
            chat_messages.append(
                Messages(role=MessagesRole.SYSTEM, content=system_instruction)
            )

        role_map = {
            "user": MessagesRole.USER,
            "assistant": MessagesRole.ASSISTANT,
            "system": MessagesRole.SYSTEM,
        }

        for message in messages:
            role = role_map.get(message.role)
            if role is None:
                raise ValueError(f"Unsupported message role: {message.role}")
            chat_messages.append(Messages(role=role, content=message.content))

        request = Chat(messages=chat_messages, model=self._model)
        response = None

        for attempt in range(2):
            try:
                response = await self._client.achat(request)
                break
            except ValidationError as exc:
                logger.warning(
                    "GigaChat SDK rejected malformed response attempt=%s model=%s error=%s",
                    attempt + 1,
                    self._model,
                    exc,
                )
                if attempt == 0:
                    self._client = self._build_client()
                    continue
                raise RuntimeError(
                    "GigaChat вернул некорректный служебный ответ. Повторите запрос."
                ) from exc

        if response is None or not response.choices:
            raise RuntimeError("GigaChat did not return a completion choice.")

        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("GigaChat returned an empty response.")

        return LLMResult(text=text, model=self._model)
