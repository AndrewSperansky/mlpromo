FROM python:3.10-slim
WORKDIR /app
COPY docker/requirements_offline /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt || pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]