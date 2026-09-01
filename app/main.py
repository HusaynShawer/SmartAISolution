import os
import sys
from contextlib import asynccontextmanager

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

for path in (APP_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from core.config import settings
from core.exceptions import register_exception_handlers
from core.logging_config import setup_logging
from core.metrics import init_metrics
from core.rate_limit import init_rate_limit
from database.session import engine
from routers import auth, chat, conversations, document, ticket

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Support Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
init_rate_limit(app)
init_metrics(app)

app.include_router(auth.api_router)
app.include_router(document.router)
app.include_router(ticket.router)
app.include_router(chat.router)
app.include_router(conversations.router)


@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": app.version,
        "database": db_status,
    }


FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount(
        "/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend"
    )
