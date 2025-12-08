# ---------- Stage: builder (устанавливаем зависимости) ----------
FROM python:3.10-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# system deps for building wheels (CatBoost / SHAP need gcc, g++)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только зависимости чтобы кешировать pip layer
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt


# ---------- Stage: runtime ----------
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app

# runtime deps for CatBoost + SHAP
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

# non-root user
RUN groupadd -r app && useradd --no-log-init -r -g app app

WORKDIR ${APP_HOME}

# копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# копируем приложение
COPY . ${APP_HOME}

# создаём каталоги для логов и моделей
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/data/models_history \
    && chown -R app:app ${APP_HOME}

# переключаемся на non-root
USER app

# переменные окружения по умолчанию (можно переопределить в compose / .env)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=INFO

# healthcheck (пинг корневого эндпоинта)
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/system/health || exit 1

# запуск FastAPI
CMD ["sh", "-c", "exec uvicorn app.main:application --host ${HOST} --port ${PORT} --workers 1"]
