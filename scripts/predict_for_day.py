# scripts/predict_for_day.py
# docker exec -it promo_ml_backend python scripts/predict_for_day.py

from datetime import date
from app.db.session import SessionLocal
from app.ml_torch.inference.predictor import TorchPredictor
from app.services.registry_service import ModelRegistryService
from pathlib import Path
import json

db = SessionLocal()

# Получаем активную LSTM модель
registry = ModelRegistryService(db)
lstm_model = registry.get_active_lstm_model()

if lstm_model:
    print(f"✅ Active LSTM model found: id={lstm_model.id}")

    # Загружаем конфиг
    meta_path = Path(lstm_model.model_path).with_suffix('.meta.json')
    with open(meta_path) as f:
        meta = json.load(f)
        model_config = meta.get("model_config", {})

    # Создаём предиктор и загружаем модель
    predictor = TorchPredictor(db)
    predictor.load_model(Path(lstm_model.model_path), model_config)

    # Тестируем прогноз на сегодня
    result = predictor.predict_for_day(
        sku="РН112367",  # Энергетик
        date=date.today(),
        store_id="00-000072"  # Какой-нибудь существующий магазин
    )

    print("\n📊 Prediction result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print("❌ No active LSTM model found")



db.close()


