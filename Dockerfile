## Dockerfile prod Вариант1

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

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    libgomp1 libstdc++6 curl  \
    && rm -rf /var/lib/apt/lists/*

# Копирование wheel файлов из builder стадии
COPY --from=builder /install/wheels /wheels

# Установка Python зависимостей
RUN pip install --no-cache-dir /wheels/*  \
    && rm -rf /wheels /root/.cache

# Копирование исходного кода приложения
COPY . /app

# копируем entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Создание non-root пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app


# Открытие порта
EXPOSE 8000

# Запуск приложения
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]