# Обзор API

Базовый URL: `/api`

## Аутентификация
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

## Дашборд
- `GET /dashboard/stats`
- `GET /dashboard/users-chart`
- `GET /dashboard/activity`

`/dashboard/stats` дополнительно возвращает:
- `new_today`, `new_week`, `new_month`
- `mailings_month`
- `active_promotions`, `active_news`, `active_deliveries`

## Пользователи
- `POST /users`
- `GET /users`
- `GET /users/{id}`
- `GET /users/stats`
- `PUT /users/{id}`
- `DELETE /users/{id}`
- `GET /users/export`

## Контент
- `GET /promotions`
- `GET /promotions/{id}`
- `POST /promotions`
- `POST /promotions/{id}/duplicate`
- `PUT /promotions/{id}`
- `DELETE /promotions/{id}`
- `GET /news`
- `GET /news/{id}`
- `POST /news`
- `PUT /news/{id}`
- `DELETE /news/{id}`
- `GET /deliveries`
- `GET /deliveries/{id}`
- `POST /deliveries`
- `PUT /deliveries/{id}`
- `DELETE /deliveries/{id}`
- `POST /upload`

## Рассылки
- `GET /mailings`
- `GET /mailings/{id}`
- `POST /mailings`
- `PUT /mailings/{id}`
- `DELETE /mailings/{id}`
- `POST /mailings/{id}/preview`
- `POST /mailings/{id}/test-send`
- `POST /mailings/{id}/send`
- `POST /mailings/{id}/cancel`
- `POST /mailings/{id}/retry`
- `GET /mailings/{id}/stats`

## Аналитика / Настройки / Логи
- `GET /analytics/users`
- `GET /analytics/mailings`
- `GET /analytics/content`
- `GET /analytics/cohort`
- `GET /analytics/conversions`
- `GET /analytics/export`
- `GET /admins`
- `POST /admins`
- `PUT /admins/{id}`
- `DELETE /admins/{id}`
- `GET /settings`
- `PUT /settings`
- `POST /settings/backup`
- `PUT /settings/backup-policy`
- `POST /settings/restore/{filename}?dry_run=true|false`
- `GET /settings/backups`
- `GET /settings/backups/{filename}`
- `GET /logs`
- `GET /logs/export`
