# app/services/dataset_streaming_service.py

import json
import logging
import uuid
import time
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.industrial_dataset import IndustrialDatasetRaw
from models.dataset_upload_history import DatasetUploadHistory

from app.schemas.dataset_schema import DatasetRecord
from app.services.ml_prediction_service import MLPredictionService

logger = logging.getLogger("promo_ml")


class DatasetStreamingService:
    """
    Service for processing streaming dataset from 1C
    Replaces CSV file upload with JSON stream
    """

    def __init__(self, ml_service: MLPredictionService):
        self.ml_service = ml_service
        self.active_batches: Dict[str, dict] = {}
        logger.info("✅ DatasetStreamingService initialized")

    async def process_stream(
        self,
        stream_generator: AsyncGenerator[bytes, None],
        db: Session
    ) -> dict:
        """
        Process streaming NDJSON data
        Saves all records to industrial_dataset_raw (single dataset)
        Tracks upload history
        """
        logger.info("🚀 process_stream STARTED")

        batch_id = str(uuid.uuid4())
        records: List[DatasetRecord] = []
        start_time = time.time()
        records_saved = 0
        error_msg = None
        status = "success"

        logger.info(f"📦 Created batch_id: {batch_id}")

        buffer = ""

        try:
            # Получаем текущее количество строк ДО загрузки
            total_before = db.query(IndustrialDatasetRaw).count()
            logger.info(f"📊 Total records before upload: {total_before}")

            async for chunk in stream_generator:
                buffer += chunk.decode('utf-8')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    logger.info(f"📨 NDJSON LINE: {line[:200]}")

                    data = json.loads(line)
                    operation = data.get("operation")
                    payload = data.get("data", {})

                    logger.info(f"Received: {operation}")

                    if operation == "batch_start":
                        total_expected = data.get("total_count")
                        logger.info(f"🎬 BATCH START: total_count={total_expected}")

                    elif operation == "record":
                        if payload:
                            # Создаём DatasetRecord из payload
                            record = DatasetRecord(
                                promo_id=payload.get("promo_id", ""),
                                week=payload.get("week", 1),
                                month=payload.get("month", 1),
                                sku=payload.get("sku", ""),
                                category=payload.get("category", ""),
                                regular_price=payload.get("regular_price", 0),
                                promo_price=payload.get("promo_price", 0),
                                store_id=payload.get("store_id", ""),
                                region=payload.get("region", ""),
                                store_location_type=payload.get("store_location_type", ""),
                                format_assortment=payload.get("format_assortment", ""),
                                adv_carrier=payload.get("adv_carrier"),
                                adv_material=payload.get("adv_material"),
                                marketing_type=payload.get("marketing_type"),
                                promo_mechanics=payload.get("promo_mechanics"),
                                analog_sku=payload.get("analog_sku"),
                                k_uplift=payload.get("k_uplift", 1.0),
                                extra_features=payload.get("extra_features")
                            )

                            records.append(record)

                            # Сохраняем в industrial_dataset_raw
                            db_record = IndustrialDatasetRaw(
                                promo_id=record.promo_id,
                                week=record.week,
                                month=record.month,
                                sku=record.sku,
                                category=record.category,
                                regular_price=record.regular_price,
                                promo_price=record.promo_price,
                                store_id=record.store_id,
                                region=record.region,
                                store_location_type=record.store_location_type,
                                format_assortment=record.format_assortment,
                                adv_carrier=record.adv_carrier,
                                adv_material=record.adv_material,
                                marketing_type=record.marketing_type,
                                promo_mechanics=record.promo_mechanics,
                                analog_sku=record.analog_sku,
                                k_uplift=record.k_uplift,
                                extra_features=record.extra_features or {},
                            )
                            db.add(db_record)
                            records_saved += 1

                            # Commit каждые 100 записей
                            if len(records) % 100 == 0:
                                db.commit()
                                logger.info(f"💾 Committed {records_saved} records to DB")

                    elif operation == "batch_end":
                        logger.info(f"🏁 BATCH END received")
                        break

                    elif operation == "error":
                        error_msg = payload.get("message", "Unknown error")
                        logger.error(f"Client error: {error_msg}")
                        status = "error"
                        break

            # Финализируем commit
            db.commit()
            logger.info(f"💾 Final commit: {records_saved} records saved")

            # =========================================================
            # CHECK RETRAIN NEED
            # =========================================================

            if status == "success":
                # Триггерим проверку необходимости retrain
                try:
                    from app.services.system_service import SystemService
                    system_service = SystemService()
                    recommendation = system_service.force_retrain()
                    logger.info(f"Retrain check completed: {recommendation}")
                except Exception as e:
                    logger.warning(f"Failed to trigger retrain check: {e}")

            # =========================================================
            # Получаем общее количество строк ПОСЛЕ загрузки
            # =========================================================

            total_after = db.query(IndustrialDatasetRaw).count()
            logger.info(f"📊 Total records after upload: {total_after}")

            duration_ms = int((time.time() - start_time) * 1000)

            # Сохраняем историю загрузки
            upload_history = DatasetUploadHistory(
                batch_id=batch_id,
                uploaded_at=datetime.now(),
                records_added=records_saved,
                total_records_after=total_after,
                status=status,
                error_message=error_msg,
                duration_ms=duration_ms
            )
            db.add(upload_history)
            db.commit()

            return {
                "batch_id": batch_id,
                "status": status,
                "records_received": len(records),
                "records_added": records_saved,
                "total_records": total_after,
                "duration_ms": duration_ms,
                "error": error_msg
            }

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            db.rollback()

            duration_ms = int((time.time() - start_time) * 1000)

            # Получаем текущее количество строк после ошибки
            total_after = db.query(IndustrialDatasetRaw).count()

            # Сохраняем ошибку в историю
            upload_history = DatasetUploadHistory(
                batch_id=batch_id,
                uploaded_at=datetime.now(),
                records_added=records_saved,
                total_records_after=total_after,
                status="error",
                error_message=str(e),
                duration_ms=duration_ms
            )
            db.add(upload_history)
            db.commit()

            return {
                "batch_id": batch_id,
                "status": "error",
                "error": str(e),
                "records_received": len(records),
                "records_added": records_saved,
                "total_records": total_after,
                "duration_ms": duration_ms
            }