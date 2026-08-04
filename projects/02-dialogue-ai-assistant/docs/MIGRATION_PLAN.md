# MONGOOSE AI PLATFORM — Migration Plan

## 1. Решение

MONGOOSE AI PLATFORM, Universal AI Bot Constructor и Knowledge & Agent Factory развиваются как один продукт, а не как три независимых проекта.

## 2. Целевая архитектура

```text
MONGOOSE AI PLATFORM
├── Platform Core
│   ├── Configuration
│   ├── Event Bus
│   ├── Audit
│   ├── Secrets
│   └── Permissions
├── Identity & Access
│   ├── Authentication
│   ├── Users
│   ├── Roles
│   ├── Sessions
│   └── MFA-ready
├── CRM Core
│   ├── Clients
│   ├── Contacts
│   ├── Organizations
│   ├── Cases
│   ├── Tasks
│   └── Operator Tickets
├── Dialogue Center
│   ├── Conversations
│   ├── Messages
│   ├── Attachments
│   ├── FSM Scenarios
│   ├── Human Handoff
│   └── Context Memory
├── Channel Gateway
│   ├── Web
│   ├── Telegram
│   ├── MAX
│   ├── VK
│   ├── Email
│   ├── WhatsApp-ready
│   └── REST API
├── Agent Runtime
│   ├── Agent Registry
│   ├── Prompt Manager
│   ├── Tool Registry
│   ├── LLM Router
│   ├── GigaChat
│   └── Guardrails
├── Knowledge Factory
│   ├── Sources
│   ├── Documents
│   ├── Chunking
│   ├── Embeddings
│   ├── Retrieval
│   ├── Claims
│   ├── Provenance
│   └── Human Verification
├── UI Engine
│   ├── Screens
│   ├── Cards
│   ├── Buttons
│   ├── Themes
│   └── Media
├── Security Center
│   ├── RBAC
│   ├── Audit Events
│   ├── File Validation
│   ├── PII Redaction
│   ├── Prompt Injection Defense
│   ├── Rate Limits
│   └── Incident Register
├── Modules
│   ├── Travel
│   ├── Hotel
│   ├── HR
│   ├── Legal
│   ├── Security Audit
│   ├── OSINT
│   ├── Regulations
│   └── Education
├── Web Portal
├── Admin Center
├── Reports
├── Monitoring
└── Deployment
    ├── Colab Demo
    ├── Docker
    └── Production Config
```

## 3. Главный принцип объединения

Все каналы используют один Application Core и одну модель данных.

```text
Telegram ─┐
MAX ──────┤
VK ───────┤
Email ────┤
Web ──────┤
API ──────┘
           ↓
     Application Core
           ↓
 CRM + Dialogue + Agent + Knowledge
```

Канал отвечает только за приём и отправку. Поиск клиента, создание диалога, регистрация сообщения, выбор агента, запуск правил и сохранение результата выполняет общее ядро.

## 4. Универсальное входящее событие

```python
IncomingMessage(
    channel="telegram",
    external_user_id="123456",
    text="Проверь поставщика ООО Ромашка",
)
```

Дальнейший конвейер:

1. найти или создать контакт;
2. создать или продолжить диалог;
3. сохранить оригинальное сообщение;
4. выбрать специализированного агента;
5. при необходимости создать кейс;
6. выполнить правила и AI-анализ;
7. сохранить результат и аудит;
8. отправить ответ через исходный канал.

## 5. Что переносим

### Из текущего веб-проекта

- Django Web Portal;
- навигацию и шаблоны;
- REST API;
- модели Conversations, Messages, Analysis и Reports;
- GigaChat provider;
- журналирование и correlation ID;
- текущую конфигурацию и тестовый веб-чат.

### Из веток ботов и Colab

- Telegram adapter;
- меню, кнопки, карточки и изображения;
- FSM;
- кеш показанных объектов;
- AI-режим;
- human handoff;
- SQLite-память как источник для миграции, но не как отдельную постоянную базу платформы;
- Colab notebooks как демонстрационный слой.

### Из Universal AI Bot Constructor

- единый формат входящего сообщения;
- интерфейсы адаптеров каналов;
- регистрацию сообщений в CRM;
- UI Engine;
- маршрутизацию к специализированным агентам;
- общий контракт Agent Module.

### Из OSINT / Knowledge Factory

- источники и документы;
- доказательства и утверждения;
- provenance;
- доверие и противоречия;
- временные линии;
- подтверждение человеком;
- сборку проверяемой базы знаний.

## 6. Роли первого релиза

| Роль | Основные возможности |
|---|---|
| Guest | Публичная часть |
| Client | Собственные диалоги и заявки |
| Operator | Обращения и ответы клиентам |
| Analyst | Кейсы, факты, документы и выводы |
| Security Specialist | Аудит, инциденты, OSINT и риски |
| Agent Developer | Агенты, промпты и сценарии |
| Administrator | Пользователи, настройки и подключения |
| Auditor | Журналы и отчёты без изменения данных |

## 7. План реализации

### Этап 0 — Inventory

- зафиксировать существующие ветки и модули;
- отметить работающие маршруты, модели, страницы и тесты;
- ничего не переписывать;
- подготовить карту переноса.

### Этап 1 — Identity & Access

Минимум для учебного релиза:

- вход и выход;
- Django User;
- группы ролей;
- защита страниц;
- аудит входа;
- MFA-ready в архитектуре, без обязательной полной реализации.

### Этап 2 — CRM Core + Dialogue Center

- ClientProfile;
- ChannelIdentity;
- Case / Ticket;
- связь Conversation с клиентом;
- общий журнал сообщений;
- operator handoff.

### Этап 3 — Telegram + Travel

- перенос рабочего Telegram adapter;
- подключение через Application Core;
- Travel Agent как контрольный модуль;
- отсутствие отдельной базы у Telegram.

### Этап 4 — Hotel + UI Engine + Cache

- карточки;
- изображения;
- кнопки;
- FSM;
- кеш объектов.

### Этап 5 — VK, MAX, Email skeleton

- общий ChannelAdapter;
- входящие и исходящие события;
- единый CRM-контакт.

### Этап 6 — Knowledge Factory + OSINT

- Sources, Documents, Claims, Provenance;
- Human Verification;
- RAG-ready;
- безопасные OSINT-сценарии.

### Этап 7 — Security Center

- RBAC;
- audit events;
- file validation;
- PII redaction;
- prompt injection controls;
- incident register;
- Top-100 controls как каталог, а не как задержка MVP.

## 8. Первый интеграционный релиз

### MONGOOSE AI PLATFORM v0.1

Планируемый состав:

- Web Portal;
- Authentication;
- Roles;
- CRM Core MVP;
- Dialogue Center;
- Telegram;
- GigaChat;
- UI Engine MVP;
- FSM;
- Travel Agent;
- Hotel Agent;
- OSINT skeleton;
- Human Handoff;
- File Upload skeleton;
- Audit Log;
- Secrets baseline;
- Colab demos;
- Docker baseline;
- GitHub Actions baseline;
- README и документация.

## 9. Правила миграции

1. Не переписывать работающий модуль без необходимости.
2. Сначала зафиксировать поведение тестом или сценарием.
3. Переносить модуль за порт/адаптер, а не напрямую связывать каналы с Django models.
4. Не создавать отдельную базу для каждого канала.
5. Секреты не хранить в Git.
6. Каждый перенос заканчивать working demo, tests, docs и commit.
7. Архитектуру заявлять полностью, реализацию делать минимально достаточной для текущего учебного задания.
