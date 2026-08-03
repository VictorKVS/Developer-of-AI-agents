import pytest

from mongoose_core.ports.llm import LLMMessage, LLMResult
from mongoose_core.services.analysis import AnalysisService, AnalysisServiceError


class FakeProvider:
    def __init__(self, text: str) -> None:
        self.text = text

    async def generate(self, messages, *, system_instruction=None):
        return LLMResult(text=self.text, model="fake-model")


@pytest.mark.asyncio
async def test_analysis_service_returns_validated_result():
    provider = FakeProvider(
        '{"summary":"Итог","facts":["Факт"],'
        '"recommendations":["Совет"],"goal":"Цель",'
        '"experience":"Опыт","interests":["AI"],'
        '"risks":[],"missing_information":[],"confidence":0.9}'
    )
    service = AnalysisService(provider)

    result = await service.analyze([LLMMessage(role="user", content="Текст")])

    assert result.summary == "Итог"
    assert result.model == "fake-model"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_analysis_service_rejects_invalid_json():
    service = AnalysisService(FakeProvider("not-json"))

    with pytest.raises(AnalysisServiceError):
        await service.analyze([LLMMessage(role="user", content="Текст")])
