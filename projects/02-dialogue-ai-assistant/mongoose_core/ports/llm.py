from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str


class LLMProvider(Protocol):
    async def generate(
        self,
        messages: Sequence[LLMMessage],
        *,
        system_instruction: str | None = None,
    ) -> LLMResult:
        """Generate a text response for the supplied conversation."""
