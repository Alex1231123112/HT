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

# Внешний S3: standalone compose без MinIO + prod-s3. Иначе — base + prod.
if [ -f docker-compose.s3-external.yml ] && grep -qE '^S3_ENDPOINT_URL=' .env 2>/dev/null; then
  COMPOSE="docker compose -f docker-compose.s3-external.yml -f docker-compose.prod-s3.yml"
else
  COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
fi
# BuildKit + кэш: npm/pip кэшируются между сборками
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
echo "=== Building images (может занять 5–10 мин) [$(date '+%H:%M:%S')] ==="
if [ "$1" = "--no-cache" ]; then
  $COMPOSE --progress=plain build --no-cache
else
  $COMPOSE --progress=plain build
fi
echo "=== Stopping old containers ==="
$COMPOSE down 2>/dev/null || true
echo "=== Starting containers ==="
$COMPOSE up -d
sleep 5
$COMPOSE exec -T api alembic upgrade head
echo "=== Done [$(date '+%H:%M:%S')]. Check: curl http://localhost:8000/health ==="
