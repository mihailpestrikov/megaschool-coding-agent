# Coding Agent

Автоматизированная система разработки на GitHub. Читает Issue, генерирует код через LLM, создаёт Pull Request, проводит AI-ревью и итеративно исправляет замечания.

## Ссылки

Видео демо [Yandex disk](https://disk.yandex.ru/d/qcj6Qj3RDniXgw)

Ссылка на тестовый проект [Github](https://github.com/mihailpestrikov/gorsk)


## Возможности

- Генерация кода по описанию задачи в Issue
- Автоматическое создание PR с описанием изменений
- AI-ревью кода с проверкой CI статуса
- Итеративное исправление по замечаниям (до 5 попыток)
- Поддержка любого LLM провайдера через LiteLLM

## Технологии

| Компонент | Библиотека | Назначение |
|-----------|------------|------------|
| CLI | [Typer](https://typer.tiangolo.com/) | Интерфейс командной строки |
| GitHub API | [PyGithub](https://pygithub.readthedocs.io/) | Работа с Issues, PR, Reviews |
| Git | [GitPython](https://gitpython.readthedocs.io/) | Клонирование, коммиты, push |
| LLM | [LiteLLM](https://docs.litellm.ai/) | Унифицированный доступ к LLM |
| Валидация | [Pydantic](https://docs.pydantic.dev/) | Структурированный вывод от LLM |
| Конфигурация | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Настройки из переменных окружения |
| Webhook сервер | [FastAPI](https://fastapi.tiangolo.com/) | GitHub App режим |

## Принцип работы

### Code Agent (генерация кода)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CODE AGENT FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

1. ПОЛУЧЕНИЕ ЗАДАЧИ
   │
   ├─► Читает Issue из GitHub (заголовок + описание)
   │
   ▼
2. СБОР КОНТЕКСТА
   │
   ├─► Анализирует структуру репозитория (дерево файлов)
   ├─► Ищет релевантные файлы по ключевым словам из Issue
   ├─► Читает содержимое найденных файлов
   │
   ▼
3. ГЕНЕРАЦИЯ КОДА
   │
   ├─► Формирует промпт: задача + контекст репозитория
   ├─► Отправляет в LLM с JSON Schema для структурированного ответа
   ├─► Получает: analysis, files[], commit_message, validation_commands[]
   │
   ▼
4. ВАЛИДАЦИЯ (опционально)
   │
   ├─► Запускает команды валидации (ruff, pytest, npm test)
   ├─► Если ошибки — отправляет их в LLM для исправления
   ├─► Повторяет до 3 раз или пока не пройдёт
   │
   ▼
5. СОЗДАНИЕ PR
   │
   ├─► Создаёт ветку agent/issue-{номер}
   ├─► Записывает/изменяет файлы
   ├─► Коммитит и пушит
   ├─► Создаёт Pull Request с описанием и метаданными
   │
   ▼
6. ГОТОВО
   └─► PR создан, ждёт ревью
```

### Reviewer Agent (ревью кода)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          REVIEWER AGENT FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

1. ПОЛУЧЕНИЕ PR
   │
   ├─► Читает PR и связанный Issue
   ├─► Получает diff изменений
   ├─► Проверяет статус CI (passed/failed)
   │
   ▼
2. АНАЛИЗ
   │
   ├─► Формирует промпт: задача + diff + CI статус
   ├─► LLM проверяет:
   │   • Решает ли код задачу из Issue?
   │   • Проходит ли CI?
   │   • Есть ли баги или проблемы безопасности?
   │   • Чистый ли код?
   │
   ▼
3. ПУБЛИКАЦИЯ REVIEW
   │
   ├─► Если всё ок → APPROVE
   ├─► Если есть замечания → REQUEST_CHANGES + комментарии
   │
   ▼
4. ИТЕРАЦИЯ (если REQUEST_CHANGES)
   │
   ├─► Code Agent читает замечания
   ├─► Генерирует исправления
   ├─► Пушит новый коммит
   ├─► Reviewer снова проверяет
   ├─► Повторяет до APPROVE или лимита итераций (5)
   │
   ▼
5. ГОТОВО
   └─► PR одобрен или помечен needs-human-review
```

### Полный цикл

```
Issue создан          Code Agent           PR создан
с лейблом ──────────► генерирует ────────► с кодом
"agent"               код                      │
                                               ▼
                                          CI запускается
                                          (lint, tests)
                                               │
                                               ▼
                      ┌──────────────────► Reviewer Agent
                      │                    анализирует
                      │                        │
                      │                   ┌────┴────┐
                      │                   ▼         ▼
                      │               APPROVE   CHANGES
                      │                   │     REQUESTED
                      │                   ▼         │
                      │                 Done        │
                      │                             ▼
                      │                      iteration < 5?
                      │                        │       │
                      │                       Yes      No
                      │                        │       │
                      └────────────────────────┘       ▼
                         Code Agent              needs-human-review
                         исправляет
```

## Установка

```bash
git clone https://github.com/your-username/coding-agent.git
cd coding-agent
pip install -e .
```

## Получение токенов

### GitHub Token (Personal Access Token)

1. Перейти: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Generate new token
3. Выбрать репозиторий
4. Permissions:
   - **Contents**: Read and write
   - **Issues**: Read and write
   - **Pull requests**: Read and write
   - **Metadata**: Read-only
5. Скопировать токен (начинается с `github_pat_` или `ghp_`)

## Конфигурация

Создать файл `.env`:

```bash
# LLM (выбрать один провайдер)
LLM_MODEL=gemini/gemini-2.5-flash
GEMINI_API_KEY=your-key

# Или OpenAI
# LLM_MODEL=gpt-4o
# OPENAI_API_KEY=sk-xxx

# Или Anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=sk-ant-xxx

# GitHub
GITHUB_TOKEN=ghp_xxx
```

## Использование

### Вариант 1: CLI (локально)

Самый простой способ — запуск из командной строки.

```bash
# Сгенерировать код по Issue
code-agent run --repo owner/repo --issue 1

# Провести ревью PR
code-agent review --repo owner/repo --pr 1

# Исправить код по замечаниям
code-agent fix --repo owner/repo --pr 1
```

Можно передать токен напрямую:
```bash
code-agent run --repo owner/repo --issue 1 --token ghp_xxx
```

### Вариант 2: Docker Compose

```bash
# Создать .env файл с переменными
cp .env.example .env
# Отредактировать .env, добавить токены

# Запустить
docker-compose run agent run --repo owner/repo --issue 1
```

### Вариант 3: GitHub Actions

Автоматический запуск при создании Issue с лейблом `agent`. Агент устанавливается из репозитория [megaschool-coding-agent](https://github.com/mihailpestrikov/megaschool-coding-agent).

**Шаг 1: Скопировать workflows в свой репозиторий**

Создать папку `.github/workflows/` и скопировать туда:
- `code_agent.yml` — запуск Code Agent на Issue
- `reviewer.yml` — запуск Reviewer на PR

```
my-project/
├── .github/
│   └── workflows/
│       ├── code_agent.yml
│       └── reviewer.yml
└── ...
```

**Шаг 2: Включить права для workflows**

Settings → Actions → General → Workflow permissions:
- Выбрать **Read and write permissions**
- Поставить галочку **Allow GitHub Actions to create and approve pull requests**
- Сохранить

**Шаг 3: Добавить секреты**

Settings → Secrets and variables → Actions → New repository secret:
- `PAT_TOKEN` — Personal Access Token с правами `repo` (нужен чтобы PR от агента запускал Reviewer workflow)
- `GEMINI_API_KEY` (или ключ другого провайдера)

Как создать PAT: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → выбрать scope `repo`

**Шаг 4: Добавить переменную модели (опционально)**

Settings → Secrets and variables → Actions → Variables → New repository variable:
- Name: `LLM_MODEL`
- Value: `gemini/gemini-2.5-flash`

**Шаг 5: Использование**

1. Создать Issue с описанием задачи
2. Добавить лейбл `agent`
3. Workflow автоматически:
   - Установит coding-agent из GitHub
   - Сгенерирует код
   - Создаст PR
   - Проведёт ревью
   - Исправит замечания

### Вариант 4: GitHub App (Server режим)

Полностью автоматический режим через GitHub App. Webhook сервер слушает события и запускает агентов.

**Шаг 1: Создать GitHub App**

1. GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
2. Заполнить:
   - **Name**: `My Coding Agent`
   - **Homepage URL**: `https://github.com/your-username/coding-agent`
   - **Webhook URL**: `https://your-server.com/webhook` (или ngrok URL)
   - **Webhook secret**: сгенерировать случайную строку
3. Permissions:
   - **Contents**: Read and write
   - **Issues**: Read and write
   - **Pull requests**: Read and write
   - **Metadata**: Read-only
4. Subscribe to events:
   - Issues
   - Pull request
   - Pull request review
5. Create GitHub App
6. Скопировать **App ID**
7. Generate private key → скачать `.pem` файл

**Шаг 2: Установить App на репозиторий**

1. Страница GitHub App → Install App
2. Выбрать репозиторий

**Шаг 3: Настроить сервер**

```bash
# .env
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY="PRIVATE KEY"
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GEMINI_API_KEY=xxx
LLM_MODEL=gemini/gemini-2.5-flash
```

**Шаг 4: Запустить сервер**

```bash
docker-compose up
```

**Шаг 5: Использование**

1. Создать Issue с лейблом `agent`
2. Webhook автоматически запустит Code Agent
3. После создания PR — запустится Reviewer
4. Цикл продолжится до одобрения

## Поддерживаемые LLM модели

Полный список: [LiteLLM Providers](https://docs.litellm.ai/docs/providers)

## Структура проекта

```
coding-agent/
├── src/coding_agent/
│   ├── cli.py              # CLI команды (run, review, fix)
│   ├── config.py           # Настройки из env
│   ├── repo_manager.py     # Клонирование репозиториев
│   ├── server.py           # Webhook сервер (GitHub App)
│   ├── agents/
│   │   ├── code_agent.py   # Генерация кода
│   │   └── reviewer_agent.py # AI ревью
│   ├── github/
│   │   ├── client.py       # GitHub API
│   │   └── app_auth.py     # JWT авторизация для App
│   ├── llm/
│   │   ├── client.py       # LiteLLM клиент
│   │   ├── prompts.py      # Промпты
│   │   └── schemas.py      # Pydantic схемы ответов
│   ├── context/
│   │   └── collector.py    # Сбор контекста репозитория
│   └── validation/
│       └── runner.py       # Запуск валидации
├── .github/workflows/
│   ├── code_agent.yml      # Workflow для Issue
│   └── reviewer.yml        # Workflow для PR
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```
