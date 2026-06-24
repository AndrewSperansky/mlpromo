# app/services/dataset_streaming_service.py

import json
import logging
import uuid
import time
from typing import AsyncGenerator, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.industrial_dataset import IndustrialDatasetRaw
from app.models.dataset_upload_history import DatasetUploadHistory

from app.schemas.dataset_schema import DatasetRecord

from app.services.ml_prediction_service import MLPredictionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("promo_ml")


class DatasetStreamingService:
    """
    Service for processing streaming dataset from 1C

    """

    def __init__(self, ml_service: MLPredictionService):
        self.ml_service = ml_service
        self.active_batches: dict = {}
        logger.info("✅ DatasetStreamingService initialized")

    async def process_stream(
            self,
            stream_generator: AsyncGenerator[bytes, None],
            db: Session,
            current_user=None
    ) -> dict:
        """
        Process streaming NDJSON data with full diagnostics
        """
        logger.info("🚀 process_stream STARTED")

        # ===== АВАРИЙНЫЙ BATCH_ID (вдруг ошибка до batch_start) =====
        batch_id = str(uuid.uuid4())
        promo_id = ""
        start_time = time.time()

        # ===== ДИАГНОСТИЧЕСКИЕ СЧЁТЧИКИ =====
        records_received = 0
        records_saved = 0
        line_number = 0
        total_expected = 0
        error_msg = None
        status = "success"

        logger.info(f"📦 Created batch_id: {batch_id}")

        buffer = b""

        try:
            # Получаем текущее количество строк ДО загрузки
            total_before = db.query(IndustrialDatasetRaw).count()
            logger.info(f"📊 Total records before upload: {total_before}")

            async for chunk in stream_generator:
                buffer += chunk  # ← байты, не строка!
                """buffer += chunk.decode("utf-8")"""

                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b"\n", 1)
                    line_number += 1
                    line = line_bytes.decode("utf-8").strip()

                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except Exception as e:
                        logger.error(f"❌ JSON ERROR line={line_number}: {e}")
                        logger.error(f"❌ BAD LINE: {line[:1000]}")
                        continue

                    operation = data.get("operation")
                    payload = data.get("data", {})

                    if operation == "batch_start":
                        # 🔥 ИСПОЛЬЗУЕМ BATCH_ID ИЗ 1С (ЕСЛИ ЕСТЬ)
                        client_batch_id = data.get("batch_id")
                        if client_batch_id:
                            batch_id = client_batch_id  # fallback
                        promo_id = data.get("promo_id", "")           # Сохраняем PROMO_ID
                        total_expected = data.get("total_count", 0)
                        logger.info(f"📌 BATCH_START line={line_number}, batch_id={batch_id}, promo_id={promo_id}")
                        logger.info(f"📌 EXPECTED RECORDS={total_expected}")
                        continue

                    if operation == "record":
                        records_received += 1

                        try:
                            # ===== ВАЛИДАЦИЯ ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ =====
                            sku = payload.get("sku", "").strip()
                            if not sku:
                                logger.warning(f"⚠️ RECORD ERROR #{records_received}: empty sku")
                                continue

                            k_uplift = payload.get("k_uplift")
                            if k_uplift is None or k_uplift <= 0:
                                logger.warning(f"⚠️ RECORD ERROR #{records_received}: k_uplift={k_uplift}, sku={sku}")
                                continue

                            promo_id = payload.get("promo_id", "").strip()
                            if not promo_id:
                                logger.warning(f"⚠️ RECORD ERROR #{records_received}: empty promo_id, sku={sku}")
                                continue

                            # ===== СОЗДАЁМ ЗАПИСЬ =====
                            record = DatasetRecord(
                                promo_id=promo_id,
                                week=payload.get("week", 1),
                                month=payload.get("month", 1),
                                sku=sku,
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
                                k_uplift=k_uplift,
                                extra_features=payload.get("extra_features")
                            )

                            # ===== СОХРАНЯЕМ В БД =====
                            db_record = IndustrialDatasetRaw(
                                batch_id=batch_id,
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
                                extra_features=record.extra_features or {}
                            )

                            db.add(db_record)
                            records_saved += 1

                            # Commit каждые 1000 записей
                            if records_saved % 1000 == 0:
                                db.commit()
                                logger.info(f"💾 SAVED={records_saved}")

                        except Exception as e:
                            logger.error(f"❌ RECORD ERROR #{records_received}: {e}")
                            logger.error(f"❌ SKU={payload.get('sku')}")
                            continue

                        continue

                    if operation == "batch_end":
                        logger.info(f"📌 BATCH_END line={line_number}")
                        continue

                    if operation == "error":
                        error_msg = payload.get("message", "Unknown error")
                        logger.error(f"❌ Client error: {error_msg}")
                        status = "error"
                        break

            # ===== ОБРАБОТКА ОСТАТКА БУФЕРА =====
            if buffer.strip():
                logger.info("📌 PROCESSING LAST BUFFER")
                try:
                    data = json.loads(buffer.decode("utf-8"))
                    logger.info(f"📌 LAST OPERATION={data.get('operation')}")
                except Exception as e:
                    logger.error(f"❌ LAST BUFFER ERROR: {e}")

            # Финализируем commit
            db.commit()
            logger.info(f"💾 Final commit: {records_saved} records saved")

            # ===== ДИАГНОСТИКА =====
            logger.info(f"📊 EXPECTED={total_expected}")
            logger.info(f"📊 RECORDS_RECEIVED={records_received}")
            logger.info(f"📊 RECORDS_SAVED={records_saved}")

            # =========================================================
            # CHECK RETRAIN NEED
            # =========================================================

            if status == "success":

                if current_user:
                    ActivityService.log(
                        db=db,
                        user_id=current_user.id,
                        action="upload_dataset",
                        resource=f"batch_{batch_id}",
                        details=f"Stream upload, records: {records_saved}"
                    )

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
                promo_id=promo_id,
                uploaded_at=datetime.now(),
                records_added=records_saved,
                total_records_after=total_after,
                status=status,
                error_message=error_msg,
                duration_ms=duration_ms
            )
            db.add(upload_history)
            db.commit()


            logger.info(f"📊 RECORDS_RECEIVED={records_received}")
            logger.info(f"📊 RECORDS_SAVED={records_saved}")
            logger.info(f"📊 EXPECTED={total_expected}")

            return {
                "batch_id": batch_id,
                "status": status,
                "records_received": records_received,
                "records_added": records_saved,
                "total_records": total_after,
                "duration_ms": duration_ms,
                "error": error_msg
            }

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            db.rollback()

            duration_ms = int((time.time() - start_time) * 1000)
            total_after = db.query(IndustrialDatasetRaw).count()

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

            logger.info(f"📊 RECORDS_RECEIVED={records_received}")
            logger.info(f"📊 RECORDS_SAVED={records_saved}")
            logger.info(f"📊 EXPECTED={total_expected}")


            return {
                "batch_id": batch_id,
                "status": "error",
                "error": str(e),
                "records_received": records_received,
                "records_added": records_saved,
                "total_records": total_after,
                "duration_ms": duration_ms
            }