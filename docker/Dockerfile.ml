FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && apt-get clean

COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только ML-часть
COPY ../app/ml /app/ml
COPY ../app/services /app/services
COPY ../data /app/data

CMD ["python", "app/ml/train.py"]
