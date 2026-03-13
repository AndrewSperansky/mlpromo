# app/main.py

from fastapi import FastAPI, Response
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
from fastapi.middleware.cors import CORSMiddleware

# ---- Routers ----
from app.api.v1.router import router as v1_router
from starlette.routing import Route

# ---- ML Runtime ----
from app.ml.contract_check import check_ml_contract
from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.self_healing.self_healing_worker import SelfHealingWorker

# ========== ДОБАВЛЕНО: для работы с БД и загрузки активной модели ==========
from app.db.session import SessionLocal
from models.ml_model import MLModel
from app.ml.model_loader import ModelLoader
# =========================================================================


# ------------------------------------------------------
# Globals
# ------------------------------------------------------

logger = logging.getLogger("promo_ml")

model_manager = ModelManager(
    check_interval=60
)

# --- создаём worker на уровне модуля (ВАЖНО) ---
self_healing_worker = SelfHealingWorker(interval_seconds=30)


# ------------------------------------------------------
# Lifespan (единственный источник lifecycle)
# ------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):

    global logger

    # ---------- STARTUP ----------
    logger = setup_logging()
    logger.info("Starting Promo ML service ...")

    # --- ML Contract check ---
    contract = check_ml_contract()
    ML_RUNTIME_STATE["checked"] = True
    ML_RUNTIME_STATE["contract"] = contract

    if contract["status"] == "ok":
        logger.info("ML contract OK", extra=contract)
    else:
        logger.warning("ML contract DEGRADED", extra=contract)

    # ========== 🔥 ВОССТАНАВЛИВАЕМ АКТИВНУЮ МОДЕЛЬ ИЗ БД ==========
    db = SessionLocal()
    try:
        # Ищем активную модель в БД
        active_model = db.query(MLModel).filter(
            MLModel.is_active == True,
            MLModel.is_deleted == False
        ).first()

        if active_model:
            logger.info(
                "✅ Active model found in DB",
                extra={
                    "model_id": active_model.id,
                    "version": active_model.version,
                    "features_count": len(active_model.features) if active_model.features else 0
                }
            )

            # Обновляем runtime state данными из БД
            ML_RUNTIME_STATE["ml_model_id"] = active_model.id
            ML_RUNTIME_STATE["version"] = active_model.version
            ML_RUNTIME_STATE["feature_order"] = active_model.features
            ML_RUNTIME_STATE["model_path"] = active_model.model_path
            ML_RUNTIME_STATE["model_loaded"] = False

            # Принудительно загружаем модель
            try:
                loaded = ModelLoader.reload()
                if loaded.get("model") is not None:
                    ML_RUNTIME_STATE["model_loaded"] = True
                    logger.info(
                        "✅ Active model loaded successfully",
                        extra={"model_id": active_model.id}
                    )
                else:
                    logger.error(
                        "❌ Failed to load active model file",
                        extra={"model_path": active_model.model_path}
                    )
            except Exception as e:
                logger.error(
                    "❌ Error loading active model",
                    extra={"error": str(e), "model_id": active_model.id}
                )
        else:
            logger.warning("⚠️ No active model found in DB, will load default")
    finally:
        db.close()
    # =================================================================

    # --- Load ML model (если не загрузили активную) ---
    if not ML_RUNTIME_STATE.get("model_loaded", False):
        try:
            model_manager.load()
            logger.info("✅ Default ML model loaded successfully")
        except FileNotFoundError:
            logger.warning("⚠️ ML model not found yet, running without ML")
        except Exception:
            logger.exception("❌ Unexpected error while loading ML model")

    # --- Start model watcher ---
    watcher_task = asyncio.create_task(model_manager.watch())
    logger.info("✅ ML watcher task started")


    # --- Start Self-Healing Worker ---
    self_healing_worker.start()
    logger.info("✅ SelfHealingWorker started")
    print("🟢 SelfHealingWorker started")

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

    # --- Stop Self-Healing Worker ---
    self_healing_worker.stop()
    logger.info("SelfHealingWorker stopped")
    print("🔴 SelfHealingWorker stopped")


# ------------------------------------------------------
# Создание FastAPI Application
# ------------------------------------------------------
app = FastAPI(
    title="Promo ML API",
    lifespan=lifespan,
    debug=True
)

# ------------------------------------------------------
# Подключение Middleware
# ------------------------------------------------------

# Разрешаем фронту обращаться к серверу
origins = [
    "http://localhost:5173",  # твой фронт
    "http://localhost:3000",  # если будешь запускать другой порт
    "http://127.0.0.1:5173",
]


# noinspection PyTypeChecker
app.add_middleware(
CORSMiddleware,
    allow_origins=origins,       # откуда разрешены запросы
    allow_credentials=True,      # куки и авторизация
    allow_methods=["*"],         # GET, POST, PUT, DELETE...
    allow_headers=["*"],         # любые заголовки
    )

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
# Routes debug endpoint
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