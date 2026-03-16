# Dockerfile

FROM python:3.10-slim

# --- Environment ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app

# --- OS dependencies ---
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libgomp1 libstdc++6 curl \
    && rm -rf /var/lib/apt/lists/*

# --- Python dependencies ---
COPY requirements/runtime.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r runtime.txt

# --- Copy application code ---
COPY . /app

# --- Entrypoint ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]