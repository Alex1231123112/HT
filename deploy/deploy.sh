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
$COMPOSE down --remove-orphans 2>/dev/null || true
echo "=== Starting containers ==="
$COMPOSE up -d --remove-orphans

# Лимиты CPU/памяти — применяем ПОСЛЕ миграций, чтобы не мешать старту
# (api/db: 512M; 384M вызывало OOM)

# Ждём готовности API (до 90 сек)
echo "=== Waiting for API health ==="
i=0
while [ $i -lt 18 ]; do
  if $COMPOSE exec -T api curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "API ready"
    break
  fi
  i=$((i + 1))
  echo "  attempt $i/18..."
  [ $i -eq 18 ] && { echo "ERROR: API health check timeout"; exit 1; }
  sleep 5
done

echo "=== Running migrations ==="
$COMPOSE exec -T api alembic upgrade head || { echo "ERROR: alembic upgrade failed"; exit 1; }
echo "=== Verifying deploy ==="
$COMPOSE exec -T api curl -sf http://127.0.0.1:8000/health || { echo "ERROR: health check failed after deploy"; exit 1; }

echo "=== Applying CPU/memory limits ==="
set +e
for svc in api bot frontend db minio; do
  cid=$($COMPOSE ps -q "$svc" 2>/dev/null)
  if [ -n "$cid" ]; then
    case $svc in
      api)   docker update --cpus=1 --memory=512m "$cid" 2>/dev/null ;;
      bot)   docker update --cpus=0.5 --memory=192m "$cid" 2>/dev/null ;;
      frontend) docker update --cpus=0.5 --memory=96m "$cid" 2>/dev/null ;;
      db)    docker update --cpus=1 --memory=512m "$cid" 2>/dev/null ;;
      minio) docker update --cpus=0.5 --memory=192m "$cid" 2>/dev/null ;;
    esac
  fi
done
set -e

echo "=== Done [$(date '+%H:%M:%S')]. API OK ==="
# Prune — без filter (until=24h давал exit 1). Отключить: ./deploy.sh --no-prune
[[ "$*" != *"--no-prune"* ]] && (docker image prune -f 2>/dev/null) || true
exit 0
