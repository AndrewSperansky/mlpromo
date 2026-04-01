# app/controllers/dataset_upload_controller.py

import logging
import uuid
import time
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

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

        logger.info(f"📤 Uploading file: {file.filename}, batch_id={batch_id}")

        # Читаем файл
        content = file.file.read()
        df = self._read_csv(content)

        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="Не удалось прочитать CSV: поддерживаются только utf-8 или cp1251"
            )

        # Проверяем наличие обязательных колонок
        required_columns = [
            'promo_id', 'sku', 'store_id', 'category', 'region',
            'store_location_type', 'format_assortment', 'month', 'week',
            'regular_price', 'promo_price', 'k_uplift'
        ]

        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing}"
            )

        # Обрабатываем данные
        records_saved = self._save_to_database(df, batch_id)

        duration_ms = int((time.time() - start_time) * 1000)

        # Получаем общее количество строк после загрузки
        total_after = self.db.query(IndustrialDatasetRaw).count()

        # Сохраняем историю
        self._save_history(batch_id, records_saved, total_after, duration_ms)

        logger.info(f"✅ Upload completed: {records_saved} records, total={total_after}, duration={duration_ms}ms")

        return {
            "batch_id": str(batch_id),
            "status": "success",
            "records_added": records_saved,
            "total_records": total_after,
            "duration_ms": duration_ms
        }

    def _read_csv(self, content: bytes) -> Optional[pd.DataFrame]:
        """Читает CSV с разными кодировками"""
        for encoding in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                df = pd.read_csv(BytesIO(content), encoding=encoding)
                logger.info(f"✅ CSV loaded with encoding: {encoding}, rows={len(df)}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading CSV: {e}")
                continue
        return None

    def _save_to_database(self, df: pd.DataFrame, batch_id: uuid.UUID) -> int:
        """Сохраняет DataFrame в industrial_dataset_raw"""
        records_saved = 0

        # Обрабатываем каждую строку
        for _, row in df.iterrows():
            try:
                # Преобразуем булевы значения
                is_new_sku = row.get('is_new_sku', False)
                if isinstance(is_new_sku, str):
                    is_new_sku = is_new_sku.lower() in ['true', '1', 'yes', 'да']

                # Создаём запись
                db_row = IndustrialDatasetRaw(
                    batch_id=batch_id,
                    promo_id=str(row.get('promo_id', '')),
                    sku=str(row.get('sku', '')),
                    store_id=str(row.get('store_id', '')),
                    category=str(row.get('category', '')),
                    region=str(row.get('region', '')),
                    store_location_type=str(row.get('store_location_type', '')),
                    format_assortment=str(row.get('format_assortment', '')),
                    month=int(row.get('month', 1)) if pd.notna(row.get('month')) else 1,
                    week=int(row.get('week', 1)) if pd.notna(row.get('week')) else 1,
                    regular_price=float(row.get('regular_price', 0)) if pd.notna(row.get('regular_price')) else 0.0,
                    promo_price=float(row.get('promo_price', 0)) if pd.notna(row.get('promo_price')) else 0.0,
                    promo_mechanics=str(row.get('promo_mechanics', '')) if pd.notna(row.get('promo_mechanics')) else '',
                    adv_carrier=str(row.get('adv_carrier', '')) if pd.notna(row.get('adv_carrier')) else '',
                    adv_material=str(row.get('adv_material', '')) if pd.notna(row.get('adv_material')) else '',
                    marketing_type=str(row.get('marketing_type', '')) if pd.notna(row.get('marketing_type')) else '',
                    analog_sku=self._parse_analog_sku(row.get('analog_sku')),
                    k_uplift=float(row.get('k_uplift', 1.0)) if pd.notna(row.get('k_uplift')) else 1.0,
                    extra_features=self._parse_extra_features(row.get('extra_features'))
                )
                self.db.add(db_row)
                records_saved += 1

                # Commit каждые 1000 записей
                if records_saved % 1000 == 0:
                    self.db.commit()
                    logger.info(f"💾 Committed {records_saved} records")

            except Exception as e:
                logger.error(f"Error saving row {records_saved + 1}: {e}")
                continue

        # Финальный commit
        self.db.commit()
        logger.info(f"✅ Saved {records_saved} records to database")

        return records_saved

    def _parse_analog_sku(self, value) -> list:
        """Парсит analog_sku в список"""
        if value is None or pd.isna(value):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            if value.strip() == '' or value.lower() == 'na':
                return []
            try:
                import json
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [parsed]
            except:
                return [value]
        return []

    def _parse_extra_features(self, value) -> dict:
        """Парсит extra_features в словарь"""
        if value is None or pd.isna(value):
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except:
                return {}
        return {}

    def _save_history(self, batch_id: uuid.UUID, records_added: int, total_after: int, duration_ms: int):
        """Сохраняет историю загрузки"""
        upload_history = DatasetUploadHistory(
            batch_id=batch_id,
            uploaded_at=datetime.now(),
            records_added=records_added,
            total_records_after=total_after,
            status="success",
            duration_ms=duration_ms
        )
        self.db.add(upload_history)
        self.db.commit()
        logger.info(f"✅ Upload history saved: batch_id={batch_id}, records={records_added}")