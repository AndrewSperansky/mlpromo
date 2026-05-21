# Dockerfile.dev2

FROM python:3.10-slim AS builder

# Замена репозиториев на российские зеркала
RUN sed -i 's/deb.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list.d/debian.sources && \
   sed -i 's/security.debian.org/mirror.yandex.ru/g' /etc/apt/sources.list.d/debian.sources

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала base (лёгкие, редко меняются)
COPY requirements/base.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r base.txt

# Потом ml (тяжёлые, редко меняются)
COPY requirements/ml.txt .
RUN pip install --no-cache-dir -r ml.txt

# --- Финальный образ ---
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Только runtime-системные зависимости (без компиляторов)
RUN apt-get update && apt-get install -y \
    libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]