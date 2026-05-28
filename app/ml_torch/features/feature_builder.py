# app/ml_torch/features/feature_builder.py

"""
Feature Builder для LSTM модели.
Собирает числовые и категориальные фичи для обучения.
"""

import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional

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
            "regular_price",  # обычная цена (не промо!)
            "quantity",  # продажи в штуках
            "revenue",  # выручка
            "sales_lag_1",  # продажи неделю назад
            "sales_lag_2",  # продажи 2 недели назад
            "sales_lag_3",  # продажи 3 недели назад
            "avg_weekly_sales",  # средние продажи за неделю
        ]

        # Категориальные фичи (для эмбеддингов)
        self.categorical_features = [
            "sku_code",  # SKU товара
            "category",  # категория
            "day_type",  # тип дня (рабочий/выходной/праздник)
            "store_code",  # ID магазина
            "region",    # Регион
            "oblast",    # Область
        ]

    def build_features_for_sku(self, sku: str, days: int = 365) -> pd.DataFrame:
        query = text("""
            SELECT 
                s.date,
                s.week,
                s.sku_code,
                s.category,
                s.quantity,
                s.revenue,
                s.store_code,         
                s.region,           
                s.oblast,       
                -- Обычная цена (не промо!)
                COALESCE(r.price, 0) as regular_price,
                -- Календарные фичи
                c.is_holiday,
                c.is_weekend,
                c.day_type,
                -- Лаговые продажи
                LAG(s.quantity, 1) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_1,
                LAG(s.quantity, 2) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_2,
                LAG(s.quantity, 3) OVER (PARTITION BY s.sku_code, s.store_code ORDER BY s.date) as sales_lag_3,
                -- Средние продажи за неделю по магазину
                AVG(s.quantity) OVER (PARTITION BY s.sku_code, s.store_code, s.week) as avg_weekly_sales
            FROM sales_fact s
            LEFT JOIN retail_price_history r 
                ON s.sku_code = r.sku_code AND s.week = r.week
            LEFT JOIN calendar c 
                ON s.date = c.date
            WHERE s.sku_code = :sku 
                AND s.date >= CURRENT_DATE - :days
            ORDER BY s.date, s.store_code
        """)

        df = pd.read_sql(query, self.db.bind, params={"sku": sku, "days": days})

        if df.empty:
            logger.warning(f"No data found for SKU={sku}")
            return df

        df = self._fill_nulls(df)

        logger.info(
            f"✅ Built {len(df)} rows with {len(self.numeric_features)} numeric + {len(self.categorical_features)} categorical features")
        logger.info(f"📊 Unique stores: {df['store_code'].nunique()}")

        return df


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