# Руководство по деплою

## Требования
- VPS с Docker и Docker Compose
- Домен + SSL-терминация (опционально для MVP)

## Шаги
1. Скопируйте `.env.example` в `.env` и заполните секреты.
   - В production задайте `APP_ENV=prod`, `ALLOWED_ORIGINS` только с `https://`.
   - Укажите `BACKUP_DIR` для хранения backup-файлов настроек.
2. Соберите и запустите: `docker compose up --build -d`
3. Примените миграции вручную: `docker compose exec api alembic upgrade head`
4. Проверьте smoke:
   - `GET /health`
   - `GET /metrics`
   - Работает вход в админ-панель
   - Бот отвечает на `/start` и `/help`

## Резервные копии
- Ежедневный backup БД: `./deploy/backup_db.ps1`.
- Проверка восстановления раз в неделю: `./deploy/restore_db.ps1 -InputFile backup.sql`.
- Еженедельный экспорт `activity_log`.
- Backup настроек: `POST /api/settings/backup`, список `GET /api/settings/backups`, скачивание `GET /api/settings/backups/{filename}`.
- Политика backup: `PUT /api/settings/backup-policy` (`schedule`, `retention_days`).
- Restore настроек: `POST /api/settings/restore/{filename}?dry_run=true|false` (сначала dry-run, затем apply).

## Частые проблемы
- Если порт PostgreSQL занят на хосте, используйте проброс `5433:5432` (уже задан в compose).
- При первом запуске дождитесь `healthcheck` БД: API и bot стартуют только после готовности `db`.

### Пользователи из бота не появляются в админке
1. **Бот должен работать в том же окружении, что и API.**  
   - Если админка и API в Docker — **бот тоже должен быть в Docker** (`docker compose up -d` поднимает api, bot, db, frontend).  
   - Если бот запускаете **локально** (`python -m bot.main`), в `.env` укажите ту же БД, что и у API в Docker:  
     `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/botdb`  
     (порт 5433 — проброс с контейнера `db` в compose.)
2. **Проверка по логам.** После `docker compose up -d` выполните:
   - `docker compose logs api 2>&1 | findstr /C:"API DB" /C:"users in DB"`  
     Должно быть: `API DB: db:5432/botdb` и `API startup: users in DB = N`.
   - `docker compose logs bot 2>&1 | findstr /C:"Bot DB"`  
     Должно быть: `Bot DB: db:5432/botdb`.  
   Если у бота видно `sqlite` или `localhost` — бот подключён к другой БД (часто из‑за локального запуска).
3. **Права в админке.** Раздел «Пользователи» доступен только ролям **admin** и **superadmin**. Вход: логин `admin`, пароль из `ADMIN_DEFAULT_PASSWORD` (по умолчанию `change-me`).
4. **Проверка по API.** После регистрации в боте откройте с авторизацией `GET /api/users/count`. Если `data.count` = 0 — API и бот пишут в разные БД или миграции не применены. В логах бота при успешной регистрации: `User registered in DB: id=...`.
5. **Миграции.** Выполните: `docker compose exec api alembic upgrade head`.

## Откат
- Используйте предыдущий тег контейнерного образа и восстановите snapshot БД.

## Pre-prod чек
- Прогнать `pytest -q` и frontend сборку.
- Проверить создание тестовой рассылки и отправку на тестовую аудиторию.
- Проверить экспорты `/api/users/export`, `/api/analytics/export`, `/api/logs/export`.
