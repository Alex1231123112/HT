# Запуск из контейнеров (Docker Compose)
# Требуется: docker compose

# Запустить все сервисы в фоне
up:
	docker compose up -d --build

# Остановить сервисы
down:
	docker compose down

# Логи API
logs-api:
	docker compose logs -f api

# --- Тесты внутри контейнера API (БД = db из compose) ---

# Все тесты
test:
	docker compose run --rm api pytest tests/ -v

# Только юнит-тесты (без БД для части тестов)
test-unit:
	docker compose run --rm api pytest tests/unit/ -v

# Только интеграционные (нужна БД; TestClient — без отдельного API на порту)
test-integration:
	docker compose run --rm api pytest tests/integration/ -v -m integration

# Тесты отправки в бот/канал (мок Telegram)
test-send:
	docker compose run --rm api pytest tests/unit/test_telegram_sender.py tests/integration/test_content_plan_send.py -v

# Smoke-тесты production (локально, PROD_URL обязателен)
test-prod:
	PROD_URL=$${PROD_URL} pytest tests/prod/ -v -m prod

# Однократный запуск команды в контейнере API (пример: make run cmd="python -c 'print(1)'")
run:
	docker compose run --rm api $(cmd)

# Ruff lint (без Docker: ruff check . — нужен Python + pip install ruff)
lint:
	docker compose run --rm api ruff check .

lint-fix:
	docker compose run --rm api ruff check . --fix

.PHONY: up down logs-api test test-unit test-integration test-send run lint lint-fix
