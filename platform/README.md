# MONGOOSE AI PLATFORM

Чистая основа единой платформы AI-агентов.

## Текущий этап

- Django 5;
- REST API;
- диалоги и сообщения;
- GigaChat через общий интерфейс LLM;
- SQLite для локального запуска;
- Python 3.10.

## Запуск

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## API

- `GET /api/v1/health/`
- `POST /api/v1/conversations/`
- `GET /api/v1/conversations/{public_id}/`
- `POST /api/v1/conversations/{public_id}/chat/`

## Принцип развития

Каждый следующий учебный проект добавляет один законченный модуль в эту платформу. Мы не создаём отдельные несвязанные приложения.
