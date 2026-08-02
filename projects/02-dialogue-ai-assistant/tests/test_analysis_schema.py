import pytest
from pydantic import ValidationError

from apps.analysis.schemas import AnalysisResult


def test_analysis_result_accepts_valid_payload():
    result = AnalysisResult.model_validate(
        {
            "profile": {
                "name": "Иван",
                "goals": ["Изучить AI-агентов"],
                "experience": "Начальный уровень",
                "interests": ["Python", "Django"],
                "constraints": ["Ограниченное время"],
            },
            "summary": "Пользователю нужен практический маршрут обучения.",
            "recommendations": [
                {
                    "title": "Собрать прототип",
                    "reason": "Практика закрепит архитектурные принципы.",
                    "next_step": "Создать первый Django endpoint.",
                }
            ],
            "confidence": 0.84,
            "missing_information": [],
            "disclaimer": "Вывод основан на доступной истории диалога.",
        }
    )

    assert result.profile.name == "Иван"
    assert result.confidence == 0.84


def test_analysis_result_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            {
                "profile": {},
                "summary": "Test",
                "recommendations": [],
                "confidence": 1.5,
                "missing_information": [],
                "disclaimer": "Test",
            }
        )
