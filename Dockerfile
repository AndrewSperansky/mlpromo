# -----------------------------------------------------
# Stage 1 — builder-base (light deps)
# -----------------------------------------------------
FROM python:3.10-slim AS builder-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /wheels

# системные пакеты (БЕЗ mount)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc g++ curl ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/project.txt /wheels/


RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --wheel-dir=/wheels -r /wheels/base.txt -r /wheels/project.txt


# -----------------------------------------------------
# Stage 2 — builder-ml (heavy deps: torch, numpy, catboost etc.)
# -----------------------------------------------------
FROM python:3.10-slim AS builder-ml

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /wheels_ml

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc g++ curl ca-certificates libgomp1 libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ml.txt /wheels_ml/

RUN pip wheel --wheel-dir=/wheels_ml -r /wheels_ml/ml.txt


# -----------------------------------------------------
# Stage 3 — runtime-builder (install wheels)
# -----------------------------------------------------
FROM python:3.10-slim AS runtime-builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
WORKDIR ${APP_HOME}

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder-base /wheels /wheels
COPY --from=builder-ml /wheels_ml /wheels_ml

# Merge wheels to prevent duplicates (narwhals, packaging, plotly, etc.)
RUN mv /wheels_ml/* /wheels/ \
    && rm -rf /wheels_ml \
    && pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels /root/.cache



# -----------------------------------------------------
# Stage 4 — final runtime
# -----------------------------------------------------
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
ENV HOST=0.0.0.0
ENV PORT=8000

WORKDIR ${APP_HOME}

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

# Создаём системного пользователя с UID=1000 и GID=1000
RUN adduser --system --group --uid 1000 --shell /bin/sh appuser

# Копируем установленный Python окружение (Copy python runtime from previous stage)
COPY --from=runtime-builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=runtime-builder /usr/local/bin /usr/local/bin

# Копируем приложение (application source)
COPY . ${APP_HOME}

# Создаём директории и назначаем владельцем appuser
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/data/models_history \
    && chown -R appuser:appuser ${APP_HOME}

# Switch to non-root user
USER 1000

# Healthcheck (СТАТИЧНЫЙ ПОРТ!)
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/system/health || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:application --host ${HOST} --port ${PORT} --workers 1"]
