# app/services/dataset_streaming_service.py

import json
import logging
import uuid
import time
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.dataset_version import DatasetVersion
from models.industrial_dataset import IndustrialDatasetRaw

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
        """Process streaming NDJSON data, save to DB, return predictions"""

        logger.info("🚀 process_stream STARTED")

        batch_id = str(uuid.uuid4())
        records: List[DatasetRecord] = []
        predictions: List[dict] = []
        total_expected = None
        start_time = time.time()
        dataset_version_id = None

        logger.info(f"📦 Created batch_id: {batch_id}")

        buffer = ""

        try:
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
                        self.active_batches[batch_id] = {
                            'total_expected': total_expected,
                            'received': 0,
                            'start_time': start_time
                        }

                        # Create dataset version
                        dataset_version = DatasetVersion(
                            id=uuid.uuid4(),
                            row_count=total_expected or 0,
                            status="LOADING"
                        )
                        db.add(dataset_version)
                        db.commit()
                        dataset_version_id = dataset_version.id
                        logger.info(f"📁 Created dataset version: {dataset_version_id}")

                    elif message.operation == "record":
                        if message.data:
                            record = message.data
                            if isinstance(record, dict):
                                record = DatasetRecord(**record)

                            records.append(record)

                            # Save to industrial_dataset_raw
                            db_record = IndustrialDatasetRaw(
                                dataset_version_id=dataset_version_id,
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
                                Date=record.Date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

                            # Commit every 100 records
                            if len(records) % 100 == 0:
                                db.commit()
                                logger.info(f"💾 Committed {len(records)} records to DB")

                            # Make prediction
                            # try:
                            #     prediction = await self._predict_record(record)
                            #     predictions.append(prediction)
                            #     logger.info(f"✅ Prediction: {prediction['prediction']} for SKU={record.SKU}")
                            # except Exception as e:
                            #     logger.error(f"Prediction failed: {e}")
                            #     predictions.append({"error": str(e), "sku": record.SKU})
                            #
                            # if batch_id in self.active_batches:
                            #     self.active_batches[batch_id]['received'] = len(records)

                    elif message.operation == "batch_end":
                        logger.info(f"🏁 BATCH END received")

                        try:
                            db.commit()
                            logger.info(f"💾 Final commit: {len(records)} records saved")
                        except Exception as e:
                            logger.error(f"Commit failed: {e}")
                            db.rollback()

                        # Update dataset version status
                        if dataset_version_id is not None:
                            try:
                                ds_id = str(dataset_version_id)
                                dataset_version = db.query(DatasetVersion).filter_by(id=ds_id).first()

                                if dataset_version:
                                    dataset_version.status = "READY"
                                    dataset_version.row_count = len(records)
                                    db.commit()
                                    logger.info(f"📁 Dataset version {ds_id} status: READY")
                                else:
                                    logger.warning(f"Dataset version {ds_id} not found")
                            except Exception as e:
                                logger.error(f"Failed to update dataset version: {e}", exc_info=True)
                                db.rollback()
                        else:
                            logger.warning("No dataset_version_id to update")

                        duration_ms = int((time.time() - start_time) * 1000)

                        return {
                            "batch_id": batch_id,
                            "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
                            "status": "success",
                            "records_received": len(records),
                            "records_saved": len(records),
                            "predictions": predictions,
                            "duration_ms": duration_ms
                        }

                    elif message.operation == "error":
                        logger.error(f"Client error: {message.error}")
                        db.rollback()
                        return {
                            "batch_id": batch_id,
                            "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
                            "status": "error",
                            "error": f"Client error: {message.error}",
                            "records_received": len(records)
                        }

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, buffer: {buffer[:200]}")
            db.rollback()
            return {
                "batch_id": batch_id,
                "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
                "status": "error",
                "error": f"Invalid JSON: {str(e)}",
                "records_received": len(records)
            }

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            db.rollback()
            return {
                "batch_id": batch_id,
                "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
                "status": "error",
                "error": str(e),
                "records_received": len(records)
            }

        # If we get here without batch_end
        db.rollback()
        return {
            "batch_id": batch_id,
            "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
            "status": "error",
            "error": "Batch end not received",
            "records_received": len(records)
        }

    async def _predict_record(self, record: DatasetRecord) -> dict:
        """Make prediction for a single record"""
        features = {
            "RegularPrice": record.RegularPrice,
            "PromoPrice": record.PromoPrice,
            "PurchasePriceBefore": record.PurchasePriceBefore,
            "PurchasePricePromo": record.PurchasePricePromo,
            "PercentPriceDrop": record.PercentPriceDrop,
            "VolumeRegular": record.VolumeRegular,
            "HistoricalSalesPromo": record.HistoricalSalesPromo,
            "SalesQty_PrevModel": record.SalesQty_PrevModel,
            "FM_Regular": record.FM_Regular,
            "FM_Promo": record.FM_Promo,
            "TurnoverBefore": record.TurnoverBefore,
            "TurnoverPromo": record.TurnoverPromo,
            "SeasonCoef_Week": record.SeasonCoef_Week,
            "ManualCoefficientFlag": record.ManualCoefficientFlag,
            "IsNewSKU": record.IsNewSKU,
            "IsAnalogSKU": record.IsAnalogSKU,
            "Store_Location_Type": record.Store_Location_Type,
            "StoreID": record.StoreID
        }

        result = self.ml_service.predict_from_features(features)

        return {
            "sku": record.SKU,
            "store_id": record.StoreID,
            "date": record.Date,
            "prediction": result["prediction"],
            "shap_values": result.get("shap_values", [])
        }

    def _format_message(self, message: StreamMessage) -> bytes:
        """Format message as NDJSON line"""
        return (json.dumps(message.model_dump(exclude_none=True), default=str, ensure_ascii=False) + "\n").encode(
            'utf-8')