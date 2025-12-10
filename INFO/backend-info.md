
ml_promo_backend/
│
├── api/                     # FastAPI роутеры
│   ├── promo/               # Роуты промо-позиций
│   ├── calculator/          # Роуты промо-калькулятора
│   ├── ml/                  # Роуты инференса модели
│   └── system/              # healthcheck, ping
│
├── core/                    # Настройки и системные модули
│   ├── config.py            # Pydantic settings
│   ├── logging_config.py    # JSON-логирование
│   ├── utils.py
│   └── errors.py
│
├── services/                # Бизнес-логика
│   ├── promo_service.py
│   ├── calculator_service.py
│   └── ml_service.py
│
├── repositories/            # Работа с БД
│   ├── promo_repo.py
│   ├── calculator_repo.py
│   └── model_repo.py
│
├── models/                  # ORM модели SQLAlchemy
│   ├── promo.py
│   ├── calculation.py
│   └── __init__.py
│
├── ml/                      # ML-инференс
│   ├── model.pkl
│   ├── inference.py
│   ├── preprocessor.py
│   └── feature_config.json
│
├── migrations/              # Alembic
│
├── tests/                   # pytest
│
├── main.py                  # Точка входа FastAPI
└── requirements.txt
