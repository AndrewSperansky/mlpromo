# scripts/aux_lstm_methods.py
# docker exec -it promo_ml_backend python scripts/aux_lstm_methods.py

from app.db.session import SessionLocal
from datetime import date, timedelta
from app.ml_torch.inference.predictor import TorchPredictor
from app.services.registry_service import ModelRegistryService


db = SessionLocal()
# Получаем активную LSTM модель
registry = ModelRegistryService(db)
# Создаём предиктор и загружаем модель
predictor = TorchPredictor(db)

# Тест _get_day_type
test_date = date(2026, 1, 1)  # Новый год
day_type = predictor._get_day_type(test_date)
print(f"Day type for {test_date}: {day_type}")  # Должен быть "Праздник"

# Тест _get_average_cheque
avg_cheque = predictor._get_average_cheque("00-000072", date.today())
print(f"Average cheque: {avg_cheque}")

# Тест _get_price_on_date
price = predictor._get_price_on_date("РН112367", date.today())
print(f"Price: {price}")

# Тест _get_sales_history
history = predictor._get_sales_history("РН112367", "00-000072", date.today())
print(f"Sales history: {history}")