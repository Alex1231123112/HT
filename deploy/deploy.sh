#!/bin/bash
# Deploy to root@147.45.96.211 - run on server: ./deploy/deploy.sh
set -e
cd "$(dirname "$0")/.."

echo "=== Deploy HT ==="
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker && systemctl start docker
fi
if ! docker compose version &>/dev/null; then
  apt-get update && apt-get install -y docker-compose-plugin || true
fi
[ ! -f .env ] && { echo "ERROR: .env not found"; exit 1; }

if [ -f docker-compose.prod.yml ]; then
  COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
else
  COMPOSE="docker compose"
fi
$COMPOSE build --no-cache
$COMPOSE up -d
sleep 5
$COMPOSE exec -T api alembic upgrade head
echo "Done. Check: curl http://localhost:8000/health"
