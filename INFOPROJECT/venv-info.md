# Создать виртуальное окружение

"D:\Program Files\Python310\python.exe" -m venv .venv

# Активировать venv

.\.venv\Scripts\activate


# Pfgecrftv ASGI-сервер.
## Он, в свою очередь, запускает FastAPI-приложение и обеспечивает

python -m uvicorn application.main:app --reload

uvicorn app.main:application --reload
