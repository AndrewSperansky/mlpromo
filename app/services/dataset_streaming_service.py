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

from app.schemas.dataset_schema import DatasetRecord, StreamMessage
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
                    message = StreamMessage(**data)

                    logger.info(f"Received: {message.operation}")

                    if message.operation == "batch_start":
                        total_expected = message.total_count
                        logger.info(f"🎬 BATCH START: total_count={total_expected}")

                    elif message.operation == "record":
                        if message.data:
                            record = message.data
                            if isinstance(record, dict):
                                record = DatasetRecord(**record)

                            records.append(record)

                            # Сохраняем в industrial_dataset_raw
                            db_record = IndustrialDatasetRaw(
                                dataset_version_id=None,
                                PromoID=record.PromoID,
                                SKU=record.SKU,
                                SKU_Level2=record.SKU_Level2,
                                SKU_Level3=record.SKU_Level3,
                                SKU_Level4=record.SKU_Level4,
                                SKU_Level5=record.SKU_Level5,
                                Category=record.Category,
                                Supplier=record.Supplier,
                                Region=record.Region,
                                StoreID=record.StoreID,
                                Store_Location_Type=record.Store_Location_Type,
                                Date=record.Date,
                                RegularPrice=record.RegularPrice,
                                PromoPrice=record.PromoPrice,
                                PurchasePriceBefore=record.PurchasePriceBefore or 0.0,
                                PurchasePricePromo=record.PurchasePricePromo or 0.0,
                                PercentPriceDrop=record.PercentPriceDrop,
                                VolumeRegular=record.VolumeRegular,
                                HistoricalSalesPromo=record.HistoricalSalesPromo,
                                SalesQty_Promo=record.SalesQty_Promo or 0.0,
                                SalesQty_PrevModel=record.SalesQty_PrevModel,
                                FM_Regular=record.FM_Regular or 0.0,
                                FM_Promo=record.FM_Promo or 0.0,
                                TurnoverBefore=record.TurnoverBefore or 0.0,
                                TurnoverPromo=record.TurnoverPromo or 0.0,
                                SeasonCoef_Week=record.SeasonCoef_Week or 0.0,
                                ManualCoefficientFlag=record.ManualCoefficientFlag or 0,
                                IsNewSKU=record.IsNewSKU or 0,
                                IsAnalogSKU=record.IsAnalogSKU or 0
                            )
                            db.add(db_record)
                            records_saved += 1

                            # Commit каждые 100 записей
                            if len(records) % 100 == 0:
                                db.commit()
                                logger.info(f"💾 Committed {records_saved} records to DB")

                    elif message.operation == "batch_end":
                        logger.info(f"🏁 BATCH END received")
                        break

                    elif message.operation == "error":
                        logger.error(f"Client error: {message.error}")
                        status = "error"
                        error_msg = f"Client error: {message.error}"
                        break

            # Финализируем commit
            db.commit()
            logger.info(f"💾 Final commit: {records_saved} records saved")

            # Получаем общее количество строк ПОСЛЕ загрузки
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