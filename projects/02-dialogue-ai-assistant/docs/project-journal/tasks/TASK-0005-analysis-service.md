# TASK-0005 — Analysis Service

## Статус

DONE

## Дата завершения

2026-08-03

## Цель

После завершения диалога проанализировать всю историю отдельным вызовом LLM и получить строго структурированный результат для сохранения в БД и последующей генерации PDF.

## Вход

Список `LLMMessage` со всей историей диалога.

## Выход

`AnalysisResult` со следующими полями:

- `summary` — краткое резюме;
- `facts` — выявленные факты;
- `recommendations` — рекомендации;
- `goal` — цель пользователя;
- `experience` — выявленный опыт;
- `interests` — интересы;
- `risks` — риски и ограничения;
- `missing_information` — недостающие сведения;
- `confidence` — уверенность анализа от 0 до 1;
- `model` — использованная модель.

## Изменённые файлы

- `mongoose_core/schemas/analysis.py`
- `mongoose_core/prompts/analysis.py`
- `mongoose_core/services/analysis.py`
- `tests/unit/test_analysis_service.py`

## Проверка

- `python manage.py check` — успешно;
- `pytest tests/unit/test_analysis_service.py -v` — 2 passed;
- Python 3.10.11;
- Django 5.2.16;
- pytest 8.4.2.

## Результат

- сервис не зависит от Django;
- LLM вызывается через `LLMProvider`;
- ответ модели валидируется Pydantic-схемой;
- поддерживается JSON в обычном виде и внутри Markdown code fence;
- невалидный ответ вызывает `AnalysisServiceError`;
- unit-тесты работают без реального обращения к GigaChat.

## Commit

`feat(analysis): add structured dialogue analysis service`

## Следующая задача

`TASK-0006 — Integrate analysis into conversation completion endpoint`.
