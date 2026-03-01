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

## Матрица тестирования

- Unit-тесты для сервисов и валидаторов
- Интеграционные тесты для auth и ключевого CRUD
- E2E smoke checklist в `tests/e2e/README.md`

## Документация

- **Описание проекта (архитектура, состав, БД, API, бот, конфиг):** [docs/PROJECT.md](docs/PROJECT.md)
- API: `docs/API.md`
- Руководство по деплою: `docs/DEPLOYMENT.md`
- Руководство администратора: `docs/ADMIN_GUIDE.md`
- Руководство пользователя бота: `docs/BOT_GUIDE.md`
