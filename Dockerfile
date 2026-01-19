# ---------- builder ----------
FROM python:3.10-slim AS builder

WORKDIR /install

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/runtime.txt .

RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir=/install/wheels -r runtime.txt


# ---------- runtime ----------
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install/wheels /wheels

RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels /root/.cache

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
