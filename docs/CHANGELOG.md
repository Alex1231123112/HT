# Журнал изменений

## 1.1.0 - 2026-02-27
- Расширен frontend админки: полный workflow рассылок (аудитория, media, schedule, preview, confirm, stats), CRUD users/content, экспорты CSV, backup UI.
- Расширены dashboard/analytics метрики (new today/week/month, monthly mailings, active content breakdown, open rate/CTR).
- Усилена безопасность: аудит неуспешных логинов, конфигурируемый rate-limit, production CORS фильтр, CSRF compare_digest, upload signature validation.
- Добавлены backup download endpoint и матрица соответствия ТЗ (`docs/TZ_TRACEABILITY.md`).
- Обновлены тесты и документация для новых сценариев.

## 1.0.0 - 2026-02-26
- Первичная реализация регистрации Telegram-бота и сегментированного меню контента.
- FastAPI backend админ-панели: auth, users, content CRUD, mailings, analytics, settings, logs.
- MVP frontend админ-панели на React: вход, пользователи, акции, рассылки.
- Docker, миграции Alembic, CI workflow, тесты и документация по деплою.
