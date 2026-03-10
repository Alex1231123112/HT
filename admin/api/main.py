import asyncio
import contextlib
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest

from admin.api.content_plan_sender import process_due_content_plans
from admin.api.routers.admins import router as admins_router
from admin.api.routers.analytics import router as analytics_router
from admin.api.routers.auth import router as auth_router
from admin.api.routers.channels import router as channels_router
from admin.api.routers.content import router as content_router
from admin.api.routers.content_plan import router as content_plan_router
from admin.api.routers.dashboard import router as dashboard_router
from admin.api.routers.establishments import router as establishments_router
from admin.api.routers.events import router as events_router
from admin.api.routers.logs import router as logs_router
from admin.api.routers.managers import router as managers_router
from admin.api.routers.settings import router as settings_router
from admin.api.routers.uploads import router as uploads_router
from admin.api.routers.users import router as users_router
from admin.api.schemas import GenericMessage
from admin.api.security import clear_revoked_tokens
from config.logging import configure_logging
from config.settings import get_settings
from database.models import User
from database.seed import ensure_default_admin, ensure_default_system_settings
from database.session import SessionLocal, engine

settings = get_settings()
configure_logging()
# CORS origins are always non-empty (settings has fallback for prod)
app = FastAPI(title="Bot Admin API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
upload_root = Path(settings.upload_dir)
upload_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_root), name="uploads")

REQ_COUNT = Counter("api_requests_total", "Total API requests", ["path", "method"])
REQ_LATENCY = Histogram("api_latency_seconds", "API latency", ["path", "method"])
_scheduler_task: asyncio.Task | None = None


def _normalize_metrics_path(path: str) -> str:
    """Сокращает кардинальность: /api/content-plan/123 -> /api/content-plan/{id}."""
    return re.sub(r"/\d+(?=/|$)", "/{id}", path) if path else "/"


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    norm_path = _normalize_metrics_path(request.url.path)
    REQ_COUNT.labels(path=norm_path, method=request.method).inc()
    REQ_LATENCY.labels(path=norm_path, method=request.method).observe((datetime.utcnow() - start).total_seconds())
    return response


def _redact_db_url(url: str) -> str:
    if "@" in url:
        return url.split("@", 1)[-1]
    return url.replace("sqlite", "sqlite***")


@app.on_event("startup")
async def startup() -> None:
    import logging

    from sqlalchemy import func, select

    clear_revoked_tokens()
    log = logging.getLogger("uvicorn.error")
    log.info("API DB: %s", _redact_db_url(settings.database_url))
    async with SessionLocal() as session:
        await ensure_default_admin(session)
        await ensure_default_system_settings(session)
        n = await session.scalar(select(func.count(User.id))) or 0
        log.info("API startup: users in DB = %s", n)
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_scheduled_content_plan_worker())


@app.on_event("shutdown")
async def shutdown() -> None:
    if _scheduler_task:
        _scheduler_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _scheduler_task
    await engine.dispose()


async def _scheduled_content_plan_worker() -> None:
    import logging
    log = logging.getLogger(__name__)
    interval = max(10, settings.content_plan_check_interval_seconds)
    while True:
        try:
            async with SessionLocal() as db:
                n = await process_due_content_plans(db, settings.bot_token)
                if n > 0:
                    log.info("Content plan worker: sent %s plan(s)", n)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.exception("Content plan worker error (will retry): %s", e)
        await asyncio.sleep(interval)


@app.get("/health", response_model=GenericMessage)
async def health() -> GenericMessage:
    return GenericMessage(message="ok")


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"))


@app.get("/api/csrf-token")
async def csrf_token() -> dict:
    """Возвращает CSRF-токен для фронтенда (same-origin, без auth)."""
    return {"token": settings.csrf_secret}


app.include_router(auth_router)
app.include_router(admins_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(establishments_router)
app.include_router(managers_router)
app.include_router(channels_router)
app.include_router(content_plan_router)
app.include_router(content_router)
app.include_router(events_router)
app.include_router(uploads_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(logs_router)
