# app/ml_torch/features/feature_builder.py

"""
Feature Builder для LSTM модели.
Собирает числовые и категориальные фичи для обучения.
"""

import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, List

logger = logging.getLogger("promo_ml")


class FeatureBuilder:
    """
    Строит фичи для LSTM модели.

    Фичи делятся на:
    1. Числовые — идут напрямую в LSTM
    2. Категориальные — проходят через эмбеддинги
    """

    def __init__(self, db: Session):
        self.db = db

        # Числовые фичи
        self.numeric_features = [
            "regular_price",      # обычная цена
            "quantity",           # продажи в штуках
            "revenue",            # выручка
            "sales_lag_1",        # продажи неделю назад
            "sales_lag_2",        # продажи 2 недели назад
            "sales_lag_3",        # продажи 3 недели назад
            "avg_weekly_sales",   # средние продажи за неделю
            "average_cheque",     # средний чек
        ]

        # Категориальные фичи (для эмбеддингов)
        self.categorical_features = [
            "sku_code",           # SKU товара
            "category",           # категория
            "day_type",           # тип дня (рабочий/выходной/праздник)
            "store_code",         # ID магазина
            "region",             # Регион
            "oblast",             # Область
        ]

    # ==========================================================
    # ДЛЯ ОДНОГО SKU
    # ==========================================================

    def build_features_for_sku(self, sku: str, days: int = 365) -> pd.DataFrame:
        """
        Строит фичи для конкретного SKU.
        """
        logger.info(f"🔨 Building features for SKU={sku}, days={days}")

        query = text("""
            SELECT 
                s.sku_code,
                s.store_code,
                s.date,
                s.week,
                s.quantity,
                s.revenue,
                s.region,
                s.oblast,
                s.category,
                COALESCE(r.price, 0) as regular_price,
                c.day_type,
                c.is_holiday,
                c.is_weekend,
                COALESCE(ac.average_amount, 0) as average_cheque,
                LAG(s.quantity, 1) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_1,
                LAG(s.quantity, 2) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_2,
                LAG(s.quantity, 3) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_3,
                AVG(s.quantity) OVER (PARTITION BY s.sku_code, s.store_code, s.week) as avg_weekly_sales
            FROM sales_fact s
            LEFT JOIN retail_price_history r 
                ON s.sku_code = r.sku_code AND s.week = r.week
            LEFT JOIN calendar c 
                ON s.date = c.date
            LEFT JOIN average_cheque ac 
                ON s.store_code = ac.store_code AND s.week = ac.week
            WHERE s.sku_code = :sku
                AND s.date >= CURRENT_DATE - :days
            ORDER BY s.date
        """)

        df = pd.read_sql(query, self.db.bind, params={"sku": sku, "days": days})

        if df.empty:
            logger.warning(f"No data found for SKU={sku}")
            return df

        df = self._fill_nulls(df)
        return df

    # ==========================================================
    # ДЛЯ ВСЕХ SKU
    # ==========================================================

    def build_features_for_all_skus(self, days: int = 365) -> pd.DataFrame:
        """
        Строит фичи для ВСЕХ SKU сразу.
        """
        logger.info(f"🔨 Building features for ALL SKUs, days={days}")

        query = text("""
            SELECT 
                s.sku_code,
                s.store_code,
                s.date,
                s.week,
                s.quantity,
                s.revenue,
                s.region,
                s.oblast,
                COALESCE(r.price, 0) as regular_price,
                c.day_type,
                c.is_holiday,
                c.is_weekend,
                COALESCE(ac.average_amount, 0) as average_cheque,
                LAG(s.quantity, 1) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_1,
                LAG(s.quantity, 2) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_2,
                LAG(s.quantity, 3) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_3,
                AVG(s.quantity) OVER (PARTITION BY s.sku_code, s.store_code, s.week) as avg_weekly_sales
            FROM sales_fact s
            LEFT JOIN retail_price_history r 
                ON s.sku_code = r.sku_code AND s.week = r.week
            LEFT JOIN calendar c 
                ON s.date = c.date
            LEFT JOIN average_cheque ac 
                ON s.store_code = ac.store_code AND s.week = ac.week
            WHERE s.date >= CURRENT_DATE - :days
            ORDER BY s.date
        """)

        df = pd.read_sql(query, self.db.bind, params={"days": days})

        logger.info(f"✅ Built features for {df['sku_code'].nunique()} SKUs, {len(df)} rows")

        if df.empty:
            return df

        df = self._fill_nulls(df)
        return df

    # ==========================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================

    def _fill_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Заполняет NULL значения"""
        # Числовые фичи → 0
        for col in self.numeric_features:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # Категориальные фичи → 'unknown'
        for col in self.categorical_features:
            if col in df.columns:
                df[col] = df[col].fillna('unknown')

        return df

    def get_feature_info(self) -> Dict:
        """Возвращает информацию о фичах для модели"""
        return {
            "numeric_features": self.numeric_features,
            "categorical_features": self.categorical_features,
            "numeric_count": len(self.numeric_features),
            "categorical_count": len(self.categorical_features),
        }