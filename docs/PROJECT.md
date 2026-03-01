# Описание проекта

Документ описывает состав, архитектуру и основные компоненты проекта: Telegram-бот, админ API, веб-админка, база данных и инфраструктура.

---

## 1. Назначение проекта

**Telegram-бот** для сегментированной аудитории (HoReCa / Розница) с:
- регистрацией пользователей (тип заведения, контакты, профиль);
- выдачей контента по типу пользователя (акции, новости, поставки, мероприятия);
- рассылками от администраторов.

**Админ-панель** (веб) для:
- управления пользователями, контентом и мероприятиями;
- создания и планирования рассылок;
- аналитики, логов и настроек;
- управления ролями (superadmin, admin, manager) и медиа (локально или S3).

---

## 2. Структура репозитория

```
├── bot/                    # Telegram-бот (aiogram 3)
│   ├── main.py             # Точка входа, polling
│   ├── handlers/           # Обработчики команд и сообщений
│   │   ├── registration.py # Регистрация, выбор типа пользователя
│   │   ├── content.py      # Показ акций, новостей, поставок, мероприятий
│   │   ├── profile.py      # Профиль, редактирование
│   │   └── fallback.py     # Обработка неизвестных сообщений
│   ├── keyboards.py        # Клавиатуры бота
│   └── utils.py            # Загрузка контента/событий из БД, отправка медиа
├── admin/
│   ├── api/                # FastAPI backend
│   │   ├── main.py         # Приложение, CORS, статика /uploads, метрики
│   │   ├── deps.py         # get_db, get_current_admin, verify_csrf
│   │   ├── security.py     # JWT, хеширование паролей (argon2)
│   │   ├── schemas.py      # Pydantic-модели запросов/ответов
│   │   ├── services.py     # Бизнес-логика (нормализация контента, экспорт и т.д.)
│   │   └── routers/
│   │       ├── auth.py     # Логин, логаут, /me, сброс пароля
│   │       ├── admins.py   # CRUD админов (superadmin)
│   │       ├── users.py    # Список/экспорт пользователей
│   │       ├── content.py  # Акции, новости, поставки (promotions, news, deliveries)
│   │       ├── events.py   # Мероприятия
│   │       ├── mailings.py # Рассылки, планирование, отправка
│   │       ├── dashboard.py# Статистика, графики, активность
│   │       ├── analytics.py# Аналитика, экспорт
│   │       ├── logs.py     # Логи активности
│   │       ├── settings.py # Системные настройки (key-value)
│   │       └── uploads.py   # Загрузка файлов (локально или S3)
│   └── frontend/           # React-админка (Vite, TypeScript, Refine, Ant Design)
│       ├── src/
│       │   ├── App.tsx     # Маршруты, Refine, ресурсы
│       │   ├── main.tsx    # Точка входа, ErrorBoundary
│       │   ├── refine/     # Провайдеры (data, auth, access), страницы Refine
│       │   ├── pages/      # Дашборд, логин, рассылки, аналитика и т.д.
│       │   ├── api.ts      # HTTP-клиент для «старого» API (если используется)
│       │   └── hooks/      # useAdminData и др.
│       ├── index.html
│       ├── vite.config.ts
│       └── package.json
├── config/
│   ├── settings.py         # Pydantic Settings (env, .env): БД, JWT, загрузки, S3, рассылки
│   └── logging.py         # Настройка логов
├── database/
│   ├── base.py             # Declarative Base SQLAlchemy
│   ├── models.py           # User, Promotion, News, Delivery, Event, Mailing, AdminUser, ActivityLog, SystemSetting
│   ├── session.py         # AsyncSession, SessionLocal
│   ├── seed.py            # Создание дефолтного админа
│   └── migrations/        # Alembic
│       └── versions/       # 0001_initial, 0002_*, 0003_user_soft_delete, 0004_bot_extended_user_and_events
├── deploy/
│   ├── Dockerfile.api      # Python, uvicorn, alembic upgrade + API
│   ├── Dockerfile.bot      # Python, bot.main
│   ├── Dockerfile.frontend # Node build + nginx
│   └── nginx.conf          # SPA: try_files $uri /index.html
├── tests/
│   ├── unit/               # test_services, test_security, test_uploads, test_settings
│   └── integration/        # test_admin_api, test_admin_flows, test_health, test_metrics, test_settings_backup
├── docker-compose.yml      # db, minio, minio-init, api, bot, frontend
├── requirements.txt        # Python-зависимости
├── .env.example             # Шаблон переменных окружения
└── docs/                   # Документация (в т.ч. этот файл)
```

---

## 3. Технологический стек

| Компонент        | Технологии |
|------------------|------------|
| Бот              | Python 3.11, aiogram 3.x |
| API              | FastAPI, uvicorn, Pydantic |
| БД               | PostgreSQL 15 (asyncpg), SQLAlchemy 2, Alembic |
| Аутентификация   | JWT (python-jose), argon2, CSRF для мутирующих запросов |
| Админка (UI)     | React 18, Vite 6, TypeScript, Refine, Ant Design 5 |
| Файлы            | Локальная папка или S3-совместимое хранилище (MinIO, boto3) |
| Планировщик      | Фоновый asyncio-цикл в API (опрос рассылок каждые 10 с) |
| Инфраструктура   | Docker Compose: PostgreSQL, MinIO, API, Bot, Frontend (nginx) |
| Наблюдаемость    | `/health`, `/metrics` (Prometheus), структурированные логи |

---

## 4. База данных (основные сущности)

- **users** — пользователи Telegram (id = Telegram user id, BigInteger): username, ФИО, телефон, дата рождения, должность, user_type (horeca/retail), establishment, registered_at, is_active, deleted_at (soft delete).
- **promotions** — акции: title, description, image_url, user_type, is_active, published_at.
- **news** — новости (аналогичная структура).
- **deliveries** — поставки (аналогичная структура).
- **events** — мероприятия: title, description, image_url, user_type, event_date, location, is_active.
- **mailings** — рассылки: text, media_url, media_type, target_type (all/horeca/retail/custom), custom_targets (JSON), scheduled_at, sent_at, status (draft/scheduled/sent/cancelled), send_attempts, last_error.
- **mailing_stats** — статистика по рассылкам (user_id, sent_at, opened_at, clicked_at).
- **admin_users** — администраторы: username, email, password_hash, role (superadmin/admin/manager), is_active.
- **activity_log** — лог действий админов (action, details, ip_address).
- **system_settings** — key-value настройки системы.

Контент и мероприятия отдаются в боте только при `is_active = true` и при совпадении аудитории (user_type = all или тип пользователя).

---

## 5. Бот: сценарии

- **Старт / команды** — приветствие, меню (акции, новости, поставки, мероприятия, профиль, написать менеджеру).
- **Регистрация** — выбор типа (HoReCa/Розница), ввод заведения и контактов; сохранение в БД, при необходимости сброс deleted_at.
- **Контент** — загрузка из БД до 5 записей по типу пользователя, отправка с медиа (фото/видео по image_url; поддержка локального URL и полного https, в т.ч. S3).
- **Профиль** — просмотр и редактирование данных.
- **Написать менеджеру** — ссылка на Telegram по `MANAGER_USERNAME`.

---

## 6. API: основные маршруты

- **Auth:** `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, сброс пароля (по необходимости).
- **Admins:** CRUD админов (доступ superadmin).
- **Users:** список пользователей, экспорт (CSV).
- **Content:** CRUD по ресурсам `/api/promotions`, `/api/news`, `/api/deliveries` (нормализация payload, фильтр полей).
- **Events:** CRUD мероприятий `/api/events`.
- **Uploads:** `POST /api/upload` (multipart, CSRF) — сохранение в локальную папку или S3; в ответе `filename`, `size`, `url`.
- **Mailings:** CRUD рассылок, планирование; фоновый воркер обрабатывает due-рассылки.
- **Dashboard:** статистика, графики пользователей, последняя активность.
- **Analytics:** отчёты, экспорт.
- **Logs:** просмотр логов активности.
- **Settings:** чтение/обновление системных настроек (key-value).

Дополнительно: `GET /health`, `GET /metrics`; раздача загруженных файлов с диска — `/uploads` (если не используется S3).

---

## 7. Админка (Frontend)

- **Вход** — логин по username/email + пароль, JWT в localStorage.
- **Разделы:** Дашборд, Пользователи, Акции / Новости / Поставки, Мероприятия, Рассылки, Аналитика, Логи, Настройки, Админы (по ролям).
- **Контент** — формы создания/редактирования с полем «Ссылка на медиа»; загрузка файла через API даёт `url`, подставляемый в медиа (работает с локальным хранилищем и S3).
- **Права:** superadmin — настройки и админы; admin/superadmin — пользователи и логи; manager — ограничённые действия по рассылкам; остальное по ролям.

Сборка: Vite, `base: "/"`. В Docker фронт собирается в образ с nginx, отдача SPA через `try_files $uri /index.html`.

---

## 8. Конфигурация (переменные окружения)

Основные переменные (см. `.env.example`):

- **Приложение:** `APP_ENV`, `APP_HOST`, `APP_PORT`, `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRES_MINUTES`, `CSRF_SECRET`.
- **Бот:** `BOT_TOKEN`, `MANAGER_USERNAME`.
- **Админка:** `ADMIN_DEFAULT_USERNAME`, `ADMIN_DEFAULT_PASSWORD`.
- **Безопасность входа:** `LOGIN_RATE_LIMIT_ATTEMPTS`, `LOGIN_RATE_LIMIT_WINDOW_MINUTES`.
- **Рассылки:** `MAILING_SEND_WINDOW_START_HOUR`, `MAILING_SEND_WINDOW_END_HOUR`, `MAILING_MIN_AUDIENCE`, `MAILING_MIN_INTERVAL_MINUTES`.
- **Загрузки:** `UPLOAD_DIR`, `UPLOAD_BASE_URL` (для локальных файлов), `MAX_UPLOAD_MB`.
- **S3 (опционально):** `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_ENDPOINT_URL`, `S3_PUBLIC_BASE_URL`. При заданных bucket и ключах загрузки идут в S3, в ответе upload возвращается полный `url`.
- **Прочее:** `TIMEZONE`, `ALLOWED_ORIGINS`, `BACKUP_DIR`; для MinIO в Docker — `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `S3_PUBLIC_BASE_URL`.

---

## 9. Docker Compose

- **db** — PostgreSQL 15, healthcheck, порт 5433→5432.
- **minio** — MinIO (S3 API на 9000, консоль на 9001).
- **minio-init** — одноразовый контейнер: создание бакета `uploads`, публичный read.
- **api** — сборка по `deploy/Dockerfile.api`; при старте `alembic upgrade head`, затем uvicorn; переменные S3 из env; зависит от db и minio-init.
- **bot** — сборка по `deploy/Dockerfile.bot`, общая с API БД.
- **frontend** — сборка Vite + nginx, порт 5173→80.

Тома: `pg_data`, `minio_data`.

---

## 10. Запуск и тесты

- **Полный стек:** `docker compose up -d --build`.
- **Локально:** `pip install -r requirements.txt`, `alembic upgrade head`, `uvicorn admin.api.main:app --reload --port 8000`, `python -m bot.main`, в отдельном терминале `cd admin/frontend && npm install && npm run dev`.
- **Тесты:** `pytest` (unit и integration); маркеры в `pytest.ini` (например `integration`).

---

## 11. Безопасность (кратко)

- JWT для API, argon2 для паролей, rate limit на логин, CORS и CSRF для мутирующих запросов.
- Роли админов (superadmin/admin/manager) и проверка прав в API и в UI.
- Секреты и ключи — только через переменные окружения, не в коде.

---

## 12. Связанные документы

- **README.md** — быстрый старт и обзор.
- **.env.example** — шаблон переменных окружения.
- При наличии: `docs/API.md`, `docs/DEPLOYMENT.md`, `docs/ADMIN_GUIDE.md`, `docs/BOT_GUIDE.md`.
