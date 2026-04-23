# Promo ML 🚀

Система машинного обучения для анализа и прогнозирования эффективности промо-акций (uplift-моделирование).

---

## 📌 Описание проекта

# Promo ML

Интеллектуальная платформа для прогнозирования эффективности промо-акций с использованием машинного обучения.

## 🚀 Основные возможности

- **ML прогнозирование** — предсказание коэффициента прироста продаж (k_uplift) с помощью CatBoost
- **Доверительные интервалы** — 95% prediction intervals на основе Conformal Prediction
- **SHAP объяснения** — интерпретация факторов, влияющих на прогноз
- **Статистическая валидация** — confidence intervals, p-value, paired t-test
- **Human-in-the-Loop** — ручное утверждение моделей перед активацией
- **Мониторинг дрифта** — SHAP drift + PSI data drift
- **Self-healing** — автоматическое обнаружение необходимости переобучения
- **Полный аудит** — логирование всех действий пользователей и предсказаний

## 🏗 Архитектура

- обучения ML моделей (CatBoost)
- оценки качества моделей (RMSE, CI, Coverage, Uplift)
- автоматического сравнения моделей
- управления жизненным циклом моделей (Model Registry + Lineage)
- визуализации метрик и мониторинга

---

## 🧠 Основная идея

Целевая переменная:

K-Uplift = PromoSales / RegularSales

Модель прогнозирует **относительный эффект промо**, а не абсолютные продажи.

---

## 🏗 Архитектура


                Frontend (Vue 3) Port 5173         
                          │  
                          ▼
                Nginx (Reverse Proxy) Port 80 
                          │
                          ▼
                Backend (FastAPI) Port 8000 
         -------------------------------------------  
         │             │             │             │  
         ▼             ▼             ▼             ▼  
    --------------------------------------------------------
      PostgreSQL │    Redis     │  Loki      │  Prometheus │
      Port 5432  │    Port 6379 │  Port 3100 │  Port 9090  │
    --------------------------------------------------------
                                │  
                                ▼  
                         Grafana Port 3000 




## 📦 Технологический стек

| Компонент  | Технологии                                  |
|------------|---------------------------------------------|
| Backend    | Python 3.10, FastAPI, SQLAlchemy            |
| ML         | CatBoost, SHAP, scikit-learn, NumPy, Pandas |
| Frontend   | Vue 3, TypeScript, Bootstrap, Chart.js      |
| Database   | PostgreSQL 15                               |
| Cache      | Redis 7                                     |
| Monitoring | Loki, Promtail, Grafana, Prometheus         |
| Container  | Docker, Docker Compose                      |
| Auth       | JWT, bcrypt                                 |

## 🚀 Быстрый старт

### Локальная разработка




# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

.venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements/requirements.txt

# Запустить бэкенд
uvicorn app.main:app --reload --port 8000

# Запустить фронтенд (в отдельном терминале)
cd frontend
npm install
npm run dev


---

## 📂 Структура моделей


/app/models
├── current/        # активная модель (production)
├── candidate/      # новые модели (до решения)
├── archive/        # архив старых моделей
├── history/        # lineage (история событий)
├── metrics/        # метрики обучения

⚙️ Основные возможности
1. Обучение модели
POST /api/v1/ml/train

Что происходит:

загрузка данных из БД
обучение CatBoost
расчёт метрик
сохранение модели
сравнение с текущей моделью


2. Сравнение моделей

📈 Метрики модели

RMSE — Root Mean Square Error  
MAE — Mean Absolute Error  
R² — Коэффициент детерминации  
Coverage — Coverage prediction intervals (target 95%)  
Uplift — Бизнес-метрика прироста  


3. Promotion (продвижение модели)

Решение:

Если новая модель лучше → становится current
Иначе → остаётся candidate


4. Lineage (история моделей)

Отслеживаются события:

training
promotion
rollback


5. Мониторинг

Используются:

Prometheus  
Grafana  
Loki  
🐳 Docker  

Dev режим
volumes:
  - ./models:/app/models

Production режим
volumes:
  - models:/app/models
 


  - 🧪 Метрики

RMSE (Root Mean Squared Error) - основная метрика ошибки.  
CI (Confidence Interval) - Интервал доверия для RMSE.  
Coverage - Показывает, насколько предсказания попадают в доверительный интервал.  
Uplift - Относительный эффект промо.  

🔥 Пример результата обучения
{
  "model_id": 277,  
  "rmse": 0.080569,  
  "coverage": 0.95,  
  "uplift": 0.0128,  
  "is_better": false  
}  

📊 Визуализация

Frontend отображает:

обучение (train/val curves)
сравнение моделей
drift + coverage
lineage

🚀 Дальнейшее развитие
PyTorch модели
временные ряды
графовые зависимости факторов
real-time inference с историей

👨‍💻 Автор
Andrey Shigaev

Проект разработан в рамках практического ML-инжиниринга.

---

