# Project Structure

```text
02-dialogue-ai-assistant/
├── apps/
│   ├── analysis/          # Вторая модель и проверка структурированного результата
│   ├── conversations/     # Диалоги, сообщения и REST API
│   └── reports/           # Брендированные PDF-отчёты
├── config/                # Настройки и маршруты Django
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HOMEWORK_2236_PRO.md
│   └── PROJECT_STRUCTURE.md
├── static/
│   └── branding/          # Логотип и стили бренда
├── templates/
│   └── reports/           # HTML-шаблон PDF
├── tests/                 # Модульные и интеграционные тесты
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Следующие файлы реализации

```text
apps/ai/providers/base.py
apps/ai/providers/gemini.py
apps/ai/services/dialogue.py
apps/analysis/services.py
apps/reports/services.py
templates/reports/user_profile.html
static/branding/logo.svg
tests/test_conversation_api.py
tests/test_analysis_schema.py
tests/test_report_generation.py
```

## Правило развития

Новый AI-провайдер или PDF-рендерер добавляется новой реализацией интерфейса. Доменные модели диалога и анализа не должны зависеть от конкретной модели Gemini или конкретной PDF-библиотеки.
