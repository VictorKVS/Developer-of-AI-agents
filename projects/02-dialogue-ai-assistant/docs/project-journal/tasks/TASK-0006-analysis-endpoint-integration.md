# TASK-0006 — Integration of Analysis into Conversation Completion

## Статус

IN PROGRESS

## Цель

Подключить `AnalysisService` к endpoint завершения диалога, проанализировать всю историю сообщений через GigaChat и сохранить результат в `UserAnalysis`.

## Вход

`POST /api/v1/conversations/{public_id}/complete/`

## Сценарий

1. Проверить существование и состояние диалога.
2. Загрузить все сообщения в правильном порядке.
3. Собрать `LLMMessage`.
4. Получить выбранный `LLMProvider` через factory.
5. Вызвать `AnalysisService.analyze()`.
6. Сохранить или обновить `UserAnalysis`.
7. Перевести диалог в статус `COMPLETED`.
8. Вернуть структурированный анализ через REST API.

## Изменяемые файлы

- `apps/conversations/views.py`
- `apps/analysis/models.py` при необходимости
- `apps/analysis/serializers.py`
- `mongoose_core/providers/factory.py` при необходимости
- интеграционные тесты endpoint.

## Definition of Done

- endpoint анализирует всю историю, а не одно сообщение;
- результат сохраняется в БД;
- повторный вызов не создаёт дубликат анализа;
- ошибки LLM переводят диалог в контролируемое состояние;
- API не раскрывает секреты и внутренний traceback;
- есть тест успешного сценария и тест ошибки провайдера.

## Commit

`feat(analysis): integrate analysis with conversation completion`
