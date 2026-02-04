# app/main.py
from fastapi import FastAPI
from fastapi import Response
from contextlib import asynccontextmanager
from app.ml.model_manager import ModelManager
import asyncio
from typing import cast, Callable
import logging

# ---- Settings ----
from app.core.settings import settings

# ---- Core Logging ----
from app.core.logging_config import setup_logging

# ---- Middleware ----
from app.middleware.logging_middleware import RequestLoggingMiddleware
# from starlette.middleware.base import BaseHTTPMiddleware

# ---- Routers ----
from app.api.v1.router import router as v1_router
from app.core.settings import settings
from starlette.routing import Route, Mount, Router

from app.ml.contract_check import check_ml_contract
from app.ml.runtime_state import ML_RUNTIME_STATE


logger = logging.getLogger("promo_ml")

model_manager = ModelManager(
    model_path=settings.ML_MODEL_PATH,
    check_interval=5
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):

    global logger

    # ---------- STARTUP ----------
    logger = setup_logging()
    logger.info("🚀 Starting Promo ML service",
                extra={
                    "env": settings.ENV,
                    "mode": "PRODUCTION" if settings.ENV == "prod" else "DEV",
                }
                )

    # --- ML Contract check ---
    contract = check_ml_contract()
    ML_RUNTIME_STATE["checked"] = True
    ML_RUNTIME_STATE["contract"] = contract

    if contract["status"] == "ok":
        logger.info("ML contract OK", extra=contract)
    else:
        logger.warning("ML contract DEGRADED", extra=contract)

    # --- Load ML model ---
    try:
        model_manager.load()
        logger.info("ML model loaded successfully")
    except FileNotFoundError:
        logger.warning("ML model not found yet, running without ML")
    except Exception:
        logger.exception("Unexpected error while loading ML model")

    # --- Start watcher ---
    watcher_task = asyncio.create_task(model_manager.watch())
    logger.info("ML watcher task started")

    # ---------- APP RUN ----------
    yield

    # ---------- SHUTDOWN ----------
    logger.info("Shutting down Promo ML service")

    if not watcher_task.done():
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            logger.info("Watcher task cancelled successfully")
        except Exception as exc:
            logger.error(
                "Error during watcher task cancellation",
                extra={"error": str(exc)},
            )



# ------------------------------------------------------
# Создание FastAPI приложения
# ------------------------------------------------------
app = FastAPI(
    title="Promo ML API",
    lifespan=lifespan,
    debug=True
)




# ------------------------------------------------------
# Подключение middleware
# ------------------------------------------------------

# noinspection PyTypeChecker
app.add_middleware(RequestLoggingMiddleware)




# ------------------------------------------------------
# Root endpoint
# ------------------------------------------------------
@app.get("/", summary="Root endpoint")
async def root():
    """Корневой эндпоинт сервиса."""
    return {"status": "ok", "service": "promo-ml"}


# ------------------------------------------------------
# Health endpoint
# ------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# ------------------------------------------------------
# Эндпоинт для просмотра всех маршрутов
# ------------------------------------------------------


@app.get("/routes", response_class=Response)
def list_routes_plain():
    lines = []

    for r in app.routes:
        if not isinstance(r, Route):
            continue

        if r.path in {
            "/openapi.json",
            "/docs",
            "/redoc",
            "/docs/oauth2-redirect",
        }:
            continue

        methods = ",".join(sorted(r.methods)) if r.methods else "-"
        name = r.name or "-"

        endpoint = cast(Callable, r.endpoint)
        module = endpoint.__module__

        line = f"{methods:<7} {r.path:<45} → {name} ({module})"
        lines.append(line)

    lines.sort()
    return Response(
        "\n".join(lines),
        media_type="text/plain; charset=utf-8"
    )



# ------------------------------------------------------
# Регистрация API v1
# ------------------------------------------------------

app.include_router(v1_router)