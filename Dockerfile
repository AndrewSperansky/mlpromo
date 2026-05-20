FROM promo-ml-backend:latest AS base

# Твой код монтируем через volumes, не пересобираем
ENV PYTHONPATH=/app

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]