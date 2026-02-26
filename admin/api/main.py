import asyncio
import contextlib
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest

from admin.api.routers.analytics import router as analytics_router
from admin.api.routers.auth import router as auth_router
from admin.api.routers.content import router as content_router
from admin.api.routers.dashboard import router as dashboard_router
from admin.api.routers.logs import router as logs_router
from admin.api.routers.mailings import process_due_mailings
from admin.api.routers.mailings import router as mailings_router
from admin.api.routers.settings import router as settings_router
from admin.api.routers.uploads import router as uploads_router
from admin.api.routers.users import router as users_router
from admin.api.schemas import GenericMessage
from config.logging import configure_logging
from config.settings import get_settings
from database.seed import ensure_default_admin
from database.session import SessionLocal

settings = get_settings()
configure_logging()
app = FastAPI(title="Bot Admin API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQ_COUNT = Counter("api_requests_total", "Total API requests", ["path", "method"])
REQ_LATENCY = Histogram("api_latency_seconds", "API latency", ["path", "method"])
_scheduler_task: asyncio.Task | None = None


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    REQ_COUNT.labels(path=request.url.path, method=request.method).inc()
    REQ_LATENCY.labels(path=request.url.path, method=request.method).observe((datetime.utcnow() - start).total_seconds())
    return response


@app.on_event("startup")
async def startup() -> None:
    async with SessionLocal() as session:
        await ensure_default_admin(session)
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_scheduled_mailing_worker())


@app.on_event("shutdown")
async def shutdown() -> None:
    if _scheduler_task:
        _scheduler_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _scheduler_task


async def _scheduled_mailing_worker() -> None:
    while True:
        async with SessionLocal() as db:
            await process_due_mailings(db)
        await asyncio.sleep(10)


@app.get("/health", response_model=GenericMessage)
async def health() -> GenericMessage:
    return GenericMessage(message="ok")


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"))

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(content_router)
app.include_router(uploads_router)
app.include_router(mailings_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(logs_router)
