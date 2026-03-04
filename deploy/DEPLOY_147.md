# Деплой на root@147.45.96.211

## CI/CD через GitHub Actions

При `push` в `main` после успешного CI автоматически запускается CD — деплой на сервер.

**Секреты в GitHub** (Settings → Secrets and variables → Actions):

| Секрет | Значение |
|--------|----------|
| `SSH_HOST` | `147.45.96.211` |
| `SSH_USER` | `root` |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ (содержимое `~/.ssh/id_ed25519` или `id_rsa`) |

**Первый раз — настройка SSH-ключа:**
```bash
# Локально: сгенерировать ключ (без пароля — дважды Enter при запросе)
ssh-keygen -t ed25519 -C "github-deploy" -f deploy_key

# Windows PowerShell: если -N "" не работает, запустите без -N и нажмите Enter при passphrase

# Публичный ключ — на сервер
ssh-copy-id -i deploy_key.pub root@147.45.96.211
# Windows: type deploy_key.pub | ssh root@147.45.96.211 "cat >> ~/.ssh/authorized_keys"

# Приватный ключ — в GitHub Secrets (скопировать вывод)
cat deploy_key
# Windows: Get-Content deploy_key
# Вставить в SSH_PRIVATE_KEY (включая строки -----BEGIN/END-----)
```

Ручной запуск: Actions → CD → Run workflow.

---

## Подготовка (локально)

1. **Создайте `.env` для production** (скопируйте `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Заполните обязательные переменные в `.env`:**
   ```
   APP_ENV=prod
   BOT_TOKEN=<токен от @BotFather>
   JWT_SECRET=<случайная строка 32+ символов>
   CSRF_SECRET=<случайная строка>
   ADMIN_DEFAULT_PASSWORD=<надёжный пароль>
   MANAGER_USERNAME=<username менеджера без @>
   
   # Доступ к админке — укажите IP или домен
   ALLOWED_ORIGINS=https://147.45.96.211,http://147.45.96.211
   
   # Медиа: Telegram должен скачивать файлы по публичному URL
   S3_PUBLIC_BASE_URL=http://147.45.96.211:9000/uploads
   UPLOAD_PUBLIC_BASE_URL=http://147.45.96.211:9000/uploads
   ```

3. **Сгенерируйте секреты:**
   ```bash
   # JWT_SECRET и CSRF_SECRET
   openssl rand -hex 32
   ```

## Первый деплой

### Вариант A: Клонирование на сервер

```bash
# На сервере
ssh root@147.45.96.211
apt update && apt install -y git
git clone <URL_РЕПОЗИТОРИЯ> /opt/ht
cd /opt/ht

# Скопируйте .env на сервер (с локальной машины):
scp .env root@147.45.96.211:/opt/ht/.env

# На сервере
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### Вариант B: Копирование архива

```bash
# Локально: создайте архив (без node_modules, .git, __pycache__)
tar --exclude=node_modules --exclude=.git --exclude=__pycache__ --exclude=.venv -czvf ht-deploy.tar.gz .

# Копируйте на сервер
scp ht-deploy.tar.gz root@147.45.96.211:/opt/
scp .env root@147.45.96.211:/opt/

# На сервере
ssh root@147.45.96.211
mkdir -p /opt/ht && cd /opt/ht
tar -xzvf ../ht-deploy.tar.gz -C .
mv ../.env . 2>/dev/null || true
sed -i 's/\r$//' deploy/deploy.sh
chmod +x deploy/deploy.sh
bash deploy/deploy.sh
```

## Порты

| Сервис   | Порт | Описание                    |
|----------|------|-----------------------------|
| Frontend | 5173 | Админка (nginx)             |
| API      | 8000 | Backend API                 |
| MinIO    | 9000 | S3-хранилище медиа          |
| MinIO UI | 9001 | Консоль MinIO (закрыть!)    |
| PostgreSQL | 5433 | БД (только localhost)     |

**Рекомендация:** Откройте в файрволе только 80 (или 5173), 8000. Порт 9001 закройте.

## SSL (опционально)

Для HTTPS настройте reverse proxy (nginx или Caddy) перед Docker:

```nginx
# /etc/nginx/sites-available/ht
server {
    listen 443 ssl;
    server_name your-domain.com;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-CSRF-Token $http_x_csrf_token;
        proxy_read_timeout 300s;
    }
}
```

Тогда в `.env`:
```
ALLOWED_ORIGINS=https://your-domain.com
S3_PUBLIC_BASE_URL=https://your-domain.com/uploads
```

## Обновление

```bash
ssh root@147.45.96.211
cd /opt/ht
git pull   # или загрузите новый архив
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose exec api alembic upgrade head
```

С `docker-compose.prod.yml`: админка на порту 80, консоль MinIO (9001) отключена.

## Резервная копия БД

```bash
docker compose exec db pg_dump -U postgres botdb > backup_$(date +%Y%m%d).sql
```

## Проверка после деплоя

- `curl http://147.45.96.211:8000/health` → `{"message":"ok"}`
- `curl http://147.45.96.211:5173` → HTML админки
- Вход в админку: логин `admin`, пароль из `ADMIN_DEFAULT_PASSWORD`
- Бот отвечает на `/start` в Telegram

## Smoke-тесты production

```bash
# Локально (нужны pytest, httpx)
PROD_URL=http://147.45.96.211:8000 pytest tests/prod/ -v -m prod

# Или через Make
make test-prod PROD_URL=http://147.45.96.211:8000
```
