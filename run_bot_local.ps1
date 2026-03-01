# Запуск бота локально с подключением к той же БД, что и API в Docker.
# Использовать, только если API и frontend подняты через docker compose (порт 5433).
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/botdb"
python -m bot.main
