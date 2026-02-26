# Руководство по деплою

## Требования
- VPS с Docker и Docker Compose
- Домен + SSL-терминация (опционально для MVP)

## Шаги
1. Скопируйте `.env.example` в `.env` и заполните секреты.
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

## Откат
- Используйте предыдущий тег контейнерного образа и восстановите snapshot БД.

## Pre-prod чек
- Прогнать `pytest -q` и frontend сборку.
- Проверить создание тестовой рассылки и отправку на тестовую аудиторию.
- Проверить экспорты `/api/users/export`, `/api/analytics/export`, `/api/logs/export`.
