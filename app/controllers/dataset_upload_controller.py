# app/controllers/dataset_upload_controller.py

import logging
import uuid
import time
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from fastapi import UploadFile, HTTPException

from models.industrial_dataset import IndustrialDatasetRaw
from models.dataset_upload_history import DatasetUploadHistory

logger = logging.getLogger("promo_ml")


class DatasetUploadController:
    """Контроллер для загрузки датасета"""

    def __init__(self, db: Session):
        self.db = db

    def upload_csv(self, file: UploadFile) -> dict:
        """
        Загружает CSV файл и добавляет данные в industrial_dataset_raw
        """
        start_time = time.time()
        batch_id = uuid.uuid4()

        # Читаем файл
        content = file.file.read()
        df = self._read_csv(content)

        if df is None:
            raise HTTPException(
                status_code=400,
                detail="Не удалось прочитать CSV: поддерживаются только utf-8 или cp1251"
            )

        # Обрабатываем данные
        df_clean = self._clean_dataframe(df)

        # Сохраняем в БД
        records_saved = self._save_to_database(df_clean)

        duration_ms = int((time.time() - start_time) * 1000)

        # Сохраняем историю
        self._save_history(batch_id, records_saved, duration_ms)

        return {
            "batch_id": str(batch_id),
            "status": "success",
            "records_added": records_saved,
            "total_records": self.db.query(IndustrialDatasetRaw).count(),
            "duration_ms": duration_ms
        }

    def _read_csv(self, content: bytes) -> Optional[pd.DataFrame]:
        """Читает CSV с разными кодировками"""
        for encoding in ("utf-8", "cp1251"):
            try:
                df = pd.read_csv(BytesIO(content), encoding=encoding)
                logger.info(f"✅ CSV loaded with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
        return None

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Очищает DataFrame: преобразует типы, заполняет NULL"""
        # Преобразуем булевы поля
        BOOL_MAP = {"Да": True, "Нет": False, "да": True, "нет": False}
        for col in ["ManualCoefficientFlag", "IsNewSKU", "IsAnalogSKU"]:
            if col in df.columns:
                df[col] = df[col].map(BOOL_MAP).fillna(False)

        # Конвертируем NaN в None
        data_for_db = []
        for _, row in df.iterrows():
            clean_row = {}
            for col_name, value in row.items():
                if pd.isna(value):
                    clean_row[col_name] = None
                else:
                    clean_row[col_name] = value
            data_for_db.append(clean_row)

        df_clean = pd.DataFrame(data_for_db)

        # Текстовые поля: NULL -> ""
        text_columns = [
            "PromoID", "SKU", "SKU_Level2", "SKU_Level3", "SKU_Level4", "SKU_Level5",
            "Category", "Supplier", "Region", "StoreID", "Store_Location_Type",
            "PromoMechanics", "PreviousPromoID", "PromoStatus", "MarketingCarrier",
            "MarketingMaterial", "FormatAssortment"
        ]

        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna("")

        # Числовые поля: NULL -> None (в БД будет NULL)
        numeric_columns = [
            "RegularPrice", "PromoPrice", "PurchasePriceBefore", "PurchasePricePromo",
            "PercentPriceDrop", "VolumeRegular", "HistoricalSalesPromo",
            "SalesQty_Promo", "SalesQty_PrevModel", "FM_Regular", "FM_Promo",
            "TurnoverBefore", "TurnoverPromo", "SeasonCoef_Week"
        ]

        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                df_clean[col] = df_clean[col].where(pd.notnull(df_clean[col]), None)

        return df_clean

    def _save_to_database(self, df: pd.DataFrame) -> int:
        """Сохраняет DataFrame в industrial_dataset_raw"""
        records_saved = 0

        for _, row in df.iterrows():
            # Создаем словарь только с нужными полями
            row_dict = {}
            for col in row.index:
                # Пропускаем служебные колонки
                if col in ['id', 'dataset_version_id']:
                    continue
                row_dict[col] = row[col] if pd.notna(row[col]) else None

            try:
                db_row = IndustrialDatasetRaw(**row_dict)
                self.db.add(db_row)
                records_saved += 1
            except Exception as e:
                logger.error(f"Error saving row: {e}")
                continue

        self.db.commit()
        logger.info(f"✅ Saved {records_saved} records to database")
        return records_saved

    def _save_history(self, batch_id: uuid.UUID, records_added: int, duration_ms: int):
        """Сохраняет историю загрузки"""
        upload_history = DatasetUploadHistory(
            batch_id=batch_id,
            uploaded_at=datetime.now(),
            records_added=records_added,
            total_records_after=self.db.query(IndustrialDatasetRaw).count(),
            status="success",
            duration_ms=duration_ms
        )
        self.db.add(upload_history)
        self.db.commit()
        logger.info(f"✅ Upload history saved: batch_id={batch_id}")