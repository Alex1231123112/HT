# Telegram-бот + Админ-панель

Production-ready MVP Telegram-бота с сегментированной выдачей контента (HoReCa/Retail), админ-панелью, рассылками, аналитикой и инфраструктурой для деплоя.

## Технологические решения

- Backend: Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic Settings
- Бот: aiogram 3.x
- База данных: PostgreSQL 15
- Очередь/планировщик: APScheduler + асинхронный фоновый опрос таблиц задач
- Frontend админки: React + Vite + TypeScript
- Инфраструктура: Docker Compose, Nginx reverse proxy
- Наблюдаемость: структурированные логи + endpoint'ы `/health` и `/metrics`

## Структура проекта

- `bot/` - обработчики Telegram-бота и точка запуска
- `admin/api/` - FastAPI backend (auth, users, content, mailings, analytics, settings, logs)
- `admin/frontend/` - React админ-панель
- `database/` - модели SQLAlchemy, миграции, seed-скрипты
- `config/` - конфигурация приложения
- `tests/` - unit и integration тесты
- `deploy/` - файлы деплоя и эксплуатационные скрипты

## Быстрый старт (Docker)

1. Скопируйте шаблон env:
   - `cp .env.example .env`
2. Укажите обязательные значения:
   - `BOT_TOKEN` — токен Telegram-бота
   - `MANAGER_USERNAME` — username менеджера без @ (для кнопки «Написать менеджеру»)
   - `UPLOAD_BASE_URL` — публичный URL загрузок (например `https://your-domain.com/uploads`), чтобы бот мог отправлять медиа
   - `JWT_SECRET`
   - `ADMIN_DEFAULT_PASSWORD`
3. Запустите:
   - `docker compose up --build`

## Локальный запуск (без Docker)

1. Создайте виртуальное окружение и установите зависимости:
   - `pip install -r requirements.txt`
2. Примените миграции БД:
   - `alembic upgrade head`
3. Запустите API:
   - `uvicorn admin.api.main:app --reload --port 8000`
4. Запустите бота:
   - `python -m bot.main`
5. Запустите frontend:
   - `cd admin/frontend && npm install && npm run dev`

## Базовые адреса API

- API: `http://localhost:8000/api`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

## CI

В GitHub Actions настроены:
- Линтинг и тесты Python
- Линтинг и сборка frontend

## Базовая безопасность

- JWT-аутентификация для админских endpoint'ов
- Хеширование паролей через `argon2`
- Rate limit для endpoint'а входа
- CORS + обязательный CSRF-заголовок для mutating-запросов
- Валидация загружаемых медиафайлов
- Хранение секретов через переменные окружения

## Запуск из контейнера

- **Поднять всё:** `docker compose up -d --build` (или `make up`)
- **Тесты в контейнере API** (БД уже есть в compose):
  - все тесты: `docker compose run --rm api pytest tests/ -v`
  - юнит: `docker compose run --rm api pytest tests/unit/ -v`
  - интеграционные: `docker compose run --rm api pytest tests/integration/ -v -m integration`
- Через Makefile: `make test`, `make test-unit`, `make test-integration`
- Windows (PowerShell): `.\scripts\run-tests-in-container.ps1` или с флагами `-Unit`, `-Integration`, `-Send`

## Матрица тестирования

- Unit-тесты для сервисов и валидаторов
- Интеграционные тесты для auth и ключевого CRUD
- Тесты отправки в бот/канал (мок Telegram): `tests/unit/test_telegram_sender.py`, `tests/integration/test_content_plan_send.py`
- E2E smoke checklist в `tests/e2e/README.md`

### Тесты отправки vs реальные сообщения

**При запуске pytest сообщения в Telegram не уходят.** Интеграционный тест `test_content_plan_send` подменяет вызовы Telegram API моками — проверяется только логика (что бы вызвалось с нужным текстом и chat_id). Так и задумано: не спамить в бот/канал при каждом прогоне тестов.

**Чтобы сообщения реально пришли в бот и канал:**

1. Запустите приложение (например `docker compose up -d` или локально API + бот).
2. В `.env` задайте рабочий `BOT_TOKEN` и при необходимости `UPLOAD_PUBLIC_BASE_URL` для медиа.
3. В админке: создайте каналы рассылки (тип «Бот» и/или «Telegram-канал» с реальным `@channel`), создайте запись контент-плана, привяжите каналы и нажмите **«Отправить»** (или вызовите `POST /api/content-plan/{id}/send` с авторизацией).
4. Убедитесь, что бот добавлен в канал как администратор (для каналов типа Telegram) и что в канале «Бот» указаны пользователи, которые уже писали боту (их id подставляются как chat_id).
5. Если в бот пришло, а в канал нет — после нажатия «Отправить» в ответе (и в уведомлении) будут показаны **ошибки Telegram** (например: «bot was kicked from the channel», «chat not found»). По ним можно исправить: добавить бота в канал с правом «Публикация сообщений», проверить @username канала в настройках канала в админке.

## Документация

- **Описание проекта (архитектура, состав, БД, API, бот, конфиг):** [docs/PROJECT.md](docs/PROJECT.md)
- API: `docs/API.md`
- Руководство по деплою: `docs/DEPLOYMENT.md`
- Руководство администратора: `docs/ADMIN_GUIDE.md`
- Руководство пользователя бота: `docs/BOT_GUIDE.md`
