# app/ml_torch/inference/predictor.py

import torch
import logging
from pathlib import Path
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.price_history_service import PriceHistoryService
from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml_torch.models.lstm import LSTMUpliftModel

logger = logging.getLogger("promo_ml")


class TorchPredictor:
    """Класс для инференса PyTorch моделей с эмбеддингами"""

    def __init__(self, db: Session):
        self.db = db
        self.price_service = PriceHistoryService(db)
        self.model = None
        self.model_config = None
        self.numeric_features = None
        self.categorical_features = None

    def load_model(self, model_path: Path, config: dict):
        """Загружает сохранённую модель с эмбеддингами"""
        logger.info(f"📋 Loading model with config: {config}")

        self.model = LSTMUpliftModel(
            numeric_features=config.get("numeric_features", 7),
            categorical_dims=config.get("categorical_dims", {}),
            embedding_dim=config.get("embedding_dim", 16),
            hidden_size=config.get("hidden_size", 64),
            num_layers=config.get("num_layers", 2),
            seq_len=config.get("seq_len", 30)
        )

        checkpoint = torch.load(model_path, map_location='cpu')

        state_dict = checkpoint.get('model_state_dict', checkpoint)
        self.model.load_state_dict(state_dict, strict=False)
        self.model.eval()
        self.model_config = config

        logger.info(f"✅ Model loaded from {model_path}")
        return self.model

    # ==========================================================
    # 🎯 ОСНОВНОЙ МЕТОД: ПРОГНОЗ НА КОНКРЕТНЫЙ ДЕНЬ
    # ==========================================================

    def predict_for_day(
            self,
            sku: str,
            date: date,
            store_id: str,
            regular_price: float = None,
            region: str = None,
            oblast: str = None,
    ) -> Dict[str, Any]:
        """Прогноз продаж для конкретного SKU и магазина на конкретный ДЕНЬ."""
        if self.model is None:
            raise ValueError("Модель не загружена. Вызовите load_model()")

        week = date.isocalendar()[1]
        day_type = self._get_day_type(date)

        if regular_price is None:
            regular_price = self._get_price_on_date(sku, date)

        history = self._get_sales_history(sku, store_id, date)

        # 🔥 НОВОЕ: получаем средний чек для магазина на эту дату
        average_cheque = self._get_average_cheque(store_id, date)

        features = {
            "regular_price": regular_price,
            "sales_lag_1": history.get("lag_1", 30),
            "sales_lag_2": history.get("lag_2", 28),
            "sales_lag_3": history.get("lag_3", 32),
            "avg_weekly_sales": history.get("avg_weekly", 30),
            "average_cheque": average_cheque,  # ← НОВАЯ ФИЧА!
            "sku_code": sku,
            "category": self._get_category(sku),
            "day_type": day_type,
            "store_code": store_id,
            "region": region or self._get_region(store_id),
            "oblast": oblast or self._get_oblast(store_id),
        }

        X_numeric, X_categorical = self._prepare_input_tensors(features)

        with torch.no_grad():
            prediction = self.model(X_numeric, X_categorical)
            predicted_quantity = float(prediction.numpy()[0])

        interval = self._get_prediction_interval(predicted_quantity)

        return {
            "predicted_quantity": round(predicted_quantity, 2),
            "interval": interval,
            "confidence": 0.95,
            "date": date.isoformat(),
            "sku": sku,
            "store_id": store_id,
        }

    # ==========================================================
    # 🛠 ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================
    # ==============================================================
    # ПОЛУЧАЕМ ТИП ДНЯ В КАЛЕНДАРЕ
    # ==============================================================

    def _get_day_type(self, target_date: date) -> str:
        """
        Возвращает тип дня из таблицы calendar.
        Типы: 'Рабочий', 'Суббота', 'Воскресенье', 'Праздник', 'Предпраздничный'
        """
        try:
            result = self.db.execute(
                text("""
                    SELECT day_type 
                    FROM calendar 
                    WHERE date = :date
                """),
                {"date": target_date}
            ).fetchone()

            if result and result[0]:
                day_type = result[0]
                logger.debug(f"Day type for {target_date} from calendar: {day_type}")
                return day_type

        except Exception as e:
            logger.warning(f"Failed to get day_type from calendar: {e}")

        # ===== FALLBACK: определяем по дню недели, если нет в календаре =====
        weekday = target_date.weekday()
        if weekday == 5:
            return "Суббота"
        elif weekday == 6:
            return "Воскресенье"
        else:
            return "Рабочий"

    # ==============================================================
    # ПОЛУЧАЕМ ЦЕНУ НА УКЗАННУЮ ДАТУ
    # ==============================================================

    def _get_price_on_date(self, sku: str, target_date: date) -> float:
        """Возвращает цену на указанную дату"""
        try:
            result = self.db.execute(
                text("""
                    SELECT price 
                    FROM retail_price_history 
                    WHERE sku_code = :sku AND date <= :date 
                    ORDER BY date DESC 
                    LIMIT 1
                """),
                {"sku": sku, "date": target_date}
            ).fetchone()
            if result:
                return float(result[0])
        except Exception as e:
            logger.warning(f"Failed to get price: {e}")
        return 100.0

    # ==============================================================
    # ПОЛУЧАЕМ ИСТОРИЮ ПРОДАЖ
    # ==============================================================

    def _get_sales_history(self, sku: str, store_id: str, target_date: date) -> dict:
        """Возвращает историю продаж для лагов (1,2,3 дня назад + среднее за неделю)"""
        result = {
            "lag_1": 30.0,
            "lag_2": 28.0,
            "lag_3": 32.0,
            "avg_weekly": 30.0,
        }

        try:
            # Получаем продажи за последние 3 дня
            rows = self.db.execute(
                text("""
                    SELECT 
                        date,
                        COALESCE(SUM(quantity), 0) as daily_qty
                    FROM sales_fact
                    WHERE sku_code = :sku 
                        AND store_code = :store_id
                        AND date >= :date - interval '3 days'
                        AND date < :date
                    GROUP BY date
                    ORDER BY date DESC
                """),
                {"sku": sku, "store_id": store_id, "date": target_date}
            ).fetchall()

            # Маппинг продаж по дням (относительно target_date)
            sales_by_day = {}
            for row in rows:
                if row[0] and row[1] is not None:
                    days_diff = (target_date - row[0]).days
                    sales_by_day[days_diff] = float(row[1])

            if 1 in sales_by_day:
                result["lag_1"] = sales_by_day[1]
            if 2 in sales_by_day:
                result["lag_2"] = sales_by_day[2]
            if 3 in sales_by_day:
                result["lag_3"] = sales_by_day[3]

            # Средние продажи за последние 7 дней
            week_result = self.db.execute(
                text("""
                    SELECT COALESCE(AVG(daily_qty), 0) as avg_qty
                    FROM (
                        SELECT 
                            date,
                            SUM(quantity) as daily_qty
                        FROM sales_fact
                        WHERE sku_code = :sku 
                            AND store_code = :store_id
                            AND date >= :date - interval '7 days'
                            AND date < :date
                        GROUP BY date
                    ) AS daily
                """),
                {"sku": sku, "store_id": store_id, "date": target_date}
            ).fetchone()

            if week_result and week_result[0] is not None and week_result[0] > 0:
                result["avg_weekly"] = float(week_result[0])

            logger.debug(
                f"Sales history for {sku}@{store_id}: lag_1={result['lag_1']}, avg_weekly={result['avg_weekly']}")

        except Exception as e:
            logger.warning(f"Failed to get sales history: {e}")

        return result

    # ==============================================================
    # ПОЛУЧАЕМ КАТЕГОРИЮ
    # ==============================================================

    def _get_category(self, sku: str) -> str:
        """Возвращает категорию SKU из retail_price_history"""
        try:
            result = self.db.execute(
                text("""
                    SELECT category 
                    FROM retail_price_history 
                    WHERE sku_code = :sku 
                        AND category IS NOT NULL 
                        AND category != ''
                    LIMIT 1
                """),
                {"sku": sku}
            ).fetchone()

            if result and result[0]:
                logger.debug(f"Category for {sku}: {result[0]}")
                return result[0]

        except Exception as e:
            logger.warning(f"Failed to get category for {sku}: {e}")

        return "ПРОЧЕЕ"

    # ==============================================================
    # ПОЛУЧАЕМ РЕГИОН
    # ==============================================================

    def _get_region(self, store_id: str) -> str:
        """Возвращает регион магазина"""
        try:
            result = self.db.execute(
                text("""
                    SELECT region 
                    FROM sales_fact 
                    WHERE store_code = :store_id 
                    LIMIT 1
                """),
                {"store_id": store_id}
            ).fetchone()
            if result and result[0]:
                return result[0]
        except Exception as e:
            logger.warning(f"Failed to get region: {e}")
        return "ФЦ"

    # ==============================================================
    # ПОЛУЧАЕМ ОБЛАСТЬ
    # ==============================================================

    def _get_oblast(self, store_id: str) -> str:
        """Возвращает область магазина из sales_fact"""
        try:
            result = self.db.execute(
                text("""
                    SELECT oblast 
                    FROM sales_fact 
                    WHERE store_code = :store_id 
                        AND oblast IS NOT NULL 
                        AND oblast != ''
                    LIMIT 1
                """),
                {"store_id": store_id}
            ).fetchone()

            if result and result[0]:
                logger.debug(f"Oblast for {store_id}: {result[0]}")
                return result[0]

        except Exception as e:
            logger.warning(f"Failed to get oblast for {store_id}: {e}")

        return "МОС_ОБЛ"  # Московская область по умолчанию

    # ==============================================================
    # ПОЛУЧАЕМ СРЕДНИЙ ЧЕК
    # ==============================================================

    def _get_average_cheque(self, store_id: str, target_date: date) -> float:
        """
        Возвращает средний чек для магазина на указанную дату.
        Индикатор платежеспособности в конкретной локации.
        """
        try:
            result = self.db.execute(
                text("""
                    SELECT average_amount
                    FROM average_cheque
                    WHERE store_code = :store_id
                        AND date <= :date
                        AND is_total = false
                    ORDER BY date DESC
                    LIMIT 1
                """),
                {"store_id": store_id, "date": target_date}
            ).fetchone()

            if result and result[0] is not None:
                avg_cheque = float(result[0])
                logger.debug(f"Average cheque for store {store_id} on {target_date}: {avg_cheque}")
                return avg_cheque

        except Exception as e:
            logger.warning(f"Failed to get average cheque for {store_id}: {e}")

        # Fallback: средний чек по умолчанию (можно взять общее среднее по всем магазинам)
        return self._get_default_average_cheque()

    def _get_default_average_cheque(self) -> float:
        """Возвращает общий средний чек по всем магазинам (fallback)"""
        try:
            result = self.db.execute(
                text("""
                    SELECT AVG(average_amount)
                    FROM average_cheque
                    WHERE is_total = false
                """)
            ).fetchone()

            if result and result[0] is not None:
                return float(result[0])

        except Exception as e:
            logger.warning(f"Failed to get default average cheque: {e}")

        return 5000.0  # Дефолтный средний чек 5000 ₽


    # ==============================================================
    # ПРЕОБРАЗОВАНИЕ ФИЧ В ТЕНЗОРЫ
    # ==============================================================

    def _prepare_input_tensors(self, features: Dict[str, Any]) -> tuple:
        """Преобразует словарь фич в тензоры для модели с эмбеддингами"""

        label_encoders = self.model_config.get("label_encoders", {})
        expected_seq_len = self.model_config.get("seq_len", 30)

        # 🔥 ПОРЯДОК КАТЕГОРИАЛЬНЫХ ФИЧ
        cat_features_order = ["sku_code", "category", "day_type", "store_code", "region", "oblast"]

        # 🔥 ПОРЯДОК ЧИСЛОВЫХ ФИЧ (ДОБАВЛЕН average_cheque)
        num_features_order = [
            "regular_price",
            "sales_lag_1",
            "sales_lag_2",
            "sales_lag_3",
            "avg_weekly_sales",
            "average_cheque"  # ← НОВАЯ ФИЧА!
        ]

        # Числовые значения
        numeric_values = []
        for col in num_features_order:
            val = features.get(col, 0)
            if isinstance(val, (int, float)):
                numeric_values.append(float(val))
            else:
                numeric_values.append(0.0)

        # Категориальные значения
        categorical_values = []
        for col in cat_features_order:
            val = features.get(col, "unknown")
            encoder = label_encoders.get(col, {})

            if isinstance(encoder, list):
                try:
                    cat_idx = encoder.index(val) if val in encoder else 0
                except ValueError:
                    cat_idx = 0
            elif isinstance(encoder, dict):
                cat_idx = encoder.get(val, 0)
            else:
                cat_idx = 0

            categorical_values.append(cat_idx)

        # Создаём тензоры
        X_numeric = torch.tensor([numeric_values], dtype=torch.float32)
        X_categorical = torch.tensor([categorical_values], dtype=torch.long)

        # Добавляем размерность seq_len
        X_numeric = X_numeric.unsqueeze(1)
        X_categorical = X_categorical.unsqueeze(1)

        # Повторяем для ожидаемой длины последовательности
        if expected_seq_len > 1:
            X_numeric = X_numeric.repeat(1, expected_seq_len, 1)
            X_categorical = X_categorical.repeat(1, expected_seq_len, 1)

        logger.debug(f"Tensors shape: numeric={X_numeric.shape}, categorical={X_categorical.shape}")

        return X_numeric, X_categorical

    # ==============================================================
    # ПОЛУЧЕНИЕ ПРОГНОЗНОГО ИНТЕРВАЛА
    # ==============================================================

    def _get_prediction_interval(self, predicted_quantity: float) -> Dict[str, float]:
        """Возвращает доверительный интервал для прогноза"""
        q_hat = ML_RUNTIME_STATE.get("conformal_q_hat")

        if q_hat is not None:
            lower = max(0, predicted_quantity - q_hat)
            upper = predicted_quantity + q_hat
            return {"lower": round(lower, 2), "upper": round(upper, 2)}
        else:
            # Дефолтный интервал ±20%
            return {
                "lower": round(predicted_quantity * 0.8, 2),
                "upper": round(predicted_quantity * 1.2, 2),
            }

    # ==========================================================
    # 📆 ОПЦИОНАЛЬНЫЙ МЕТОД: ПРОГНОЗ НА НЕДЕЛЮ
    # ==========================================================

    def predict_for_week(
            self,
            sku: str,
            week: int,
            year: int,
            store_id: str,
            regular_price: float = None,
    ) -> Dict[str, Any]:
        """Прогноз продаж на неделю (среднедневные продажи)."""
        from datetime import datetime
        first_day = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()

        daily_predictions = []
        for day_offset in range(7):
            day = first_day + timedelta(days=day_offset)
            result = self.predict_for_day(sku, day, store_id, regular_price)
            daily_predictions.append(result["predicted_quantity"])

        avg_weekly = sum(daily_predictions) / 7

        return {
            "predicted_quantity_weekly": round(avg_weekly * 7, 2),
            "predicted_quantity_daily_avg": round(avg_weekly, 2),
            "daily_breakdown": daily_predictions,
            "week": week,
            "year": year,
            "sku": sku,
            "store_id": store_id,
        }