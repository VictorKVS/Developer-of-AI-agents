# Architecture

## Scope

Первая версия реализует ДЗ 2236 PRO, но границы модулей выбираются так, чтобы проект стал частью универсальной платформы AI-агентов.

## Components

```text
Web Client
    │
    ▼
Django REST API
    │
    ├── conversations — сессии и сообщения
    ├── ai — провайдеры и диалоговая модель
    ├── analysis — отдельная аналитическая модель
    └── reports — брендированный PDF и скачивание
```

## Separation of concerns

### Dialogue service

Отвечает только за продолжение разговора. Получает историю и новое сообщение, возвращает очередной ответ ассистента.

### Analysis service

Запускается после завершения диалога. Получает неизменяемую историю, возвращает JSON по строгой Pydantic-схеме. Не должен подменяться простым копированием собранных полей.

### Report service

Не обращается к AI напрямую. Получает проверенный `AnalysisResult`, подставляет его в брендированный HTML-шаблон и формирует PDF.

## Reliability rules

- завершение диалога идемпотентно;
- сообщения имеют уникальный порядковый номер внутри сессии;
- невалидный JSON модели не попадает в отчёт;
- ошибка аналитики переводит сессию в `FAILED` и сохраняется в журнале;
- PDF создаётся только после успешной проверки результата;
- API-ключи читаются только из переменных окружения.

## Planned interfaces

```python
class BaseAIProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class DialogueService(Protocol):
    def reply(self, history: list[dict[str, str]]) -> str: ...


class AnalysisService(Protocol):
    def analyze(self, history: list[dict[str, str]]) -> AnalysisResult: ...


class ReportRenderer(Protocol):
    def render(self, analysis: AnalysisResult) -> bytes: ...
```

## Future platform integration

Следующие слои подключаются без изменения предметных моделей:

- Telegram и другие канальные адаптеры;
- Celery и Redis;
- PostgreSQL;
- база знаний и RAG;
- pgvector;
- реестр агентов;
- маршрутизатор задач;
- аудит и RBAC;
- резервные AI-провайдеры.
