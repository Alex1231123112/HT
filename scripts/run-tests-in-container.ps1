# Запуск тестов из контейнера API (Docker Compose)
# Использование:
#   .\scripts\run-tests-in-container.ps1           # все тесты
#   .\scripts\run-tests-in-container.ps1 -Unit     # только unit
#   .\scripts\run-tests-in-container.ps1 -Integration  # только integration

param(
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Send
)

Set-Location $PSScriptRoot\..

if ($Unit) {
    docker compose run --rm api pytest tests/unit/ -v
} elseif ($Integration) {
    docker compose run --rm api pytest tests/integration/ -v -m integration
} elseif ($Send) {
    docker compose run --rm api pytest tests/unit/test_telegram_sender.py tests/integration/test_content_plan_send.py -v
} else {
    docker compose run --rm api pytest tests/ -v
}
