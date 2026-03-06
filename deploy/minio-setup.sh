#!/bin/bash
# Настройка MinIO: создание bucket uploads и публичный доступ
# Запуск: ./deploy/minio-setup.sh (из /opt/ht на сервере)
# Берёт MINIO_ROOT_USER и MINIO_ROOT_PASSWORD из .env
set -e
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && source .env && set +a

USER="${MINIO_ROOT_USER:-minioadmin}"
PASS="${MINIO_ROOT_PASSWORD:-minioadmin}"

docker run --rm --network container:ht-api-1 \
  -e MINIO_ROOT_USER="$USER" -e MINIO_ROOT_PASSWORD="$PASS" \
  --entrypoint /bin/sh minio/mc -c '
    mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
    mc mb myminio/uploads --ignore-existing
    mc anonymous set download myminio/uploads
    echo "Bucket uploads ready"
    mc ls myminio/uploads/ 2>/dev/null || echo "(bucket empty)"
'
