# TASK-0005 — Analysis Service

## Статус

IN PROGRESS

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

## Изменяемые файлы

- `mongoose_core/schemas/analysis.py`
- `mongoose_core/prompts/analysis.py`
- `mongoose_core/services/analysis.py`
- `tests/unit/test_analysis_service.py`

## Definition of Done

- сервис не зависит от Django;
- LLM вызывается через `LLMProvider`;
- ответ модели валидируется Pydantic-схемой;
- поддерживается JSON в обычном виде и внутри Markdown code fence;
- невалидный ответ вызывает понятную ошибку;
- есть unit-тест без реального обращения к GigaChat;
- после локальной проверки задача переводится в DONE.

## Commit

`feat(analysis): add structured dialogue analysis service`
