# scripts/send_final.py

import requests
import json

messages = [
    {"operation": "batch_start", "batch_id": "test-РН229840-001", "total_count": 1},
    {
        "operation": "record",
        "data": {
            "PromoID": "Промо-1-2026",
            "SKU": "РН229840",
            "SKU_Level2": "0Q06",
            "SKU_Level3": "0Q0601",
            "SKU_Level4": "0Q060101",
            "SKU_Level5": "",
            "Category": "Охлажденка",
            "Supplier": "ООО РЫБАСОЛЬ",
            "Region": "МСК",
            "Store_Location_Type": "Спальный",
            "Date": "16.01.2026 00:00:00",
            "StoreID": "МГЗ №271",
            "RegularPrice": 259.99,
            "PromoPrice": 229.99,
            "PurchasePriceBefore": 116.71,
            "PurchasePricePromo": 116.71,
            "PercentPriceDrop": 11.54,
            "VolumeRegular": 119.86,
            "HistoricalSalesPromo": 442,
            "SalesQty_Promo": 5,
            "SalesQty_PrevModel": 1.25,
            "FM_Regular": 50.62,
            "FM_Promo": 44.18,
            "TurnoverBefore": 31162.4,
            "TurnoverPromo": 28898.24,
            "SeasonCoef_Week": 0,
            "ManualCoefficientFlag": 0,
            "IsNewSKU": 0,
            "IsAnalogSKU": 0,
            "PromoMechanics": "промо-23-2025",
            "PreviousPromoID": "",
            "PromoStatus": "ЖЦ",
            "MarketingCarrier": "",
            "MarketingMaterial": "",
            "FormatAssortment": ""
        }
    },
    {"operation": "batch_end", "batch_id": "test-РН229840-001"}
]

# Формируем NDJSON
data = "\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n"

print("📤 Sending data:")
print(data)
print("-" * 50)

response = requests.post(
    "http://localhost:8000/api/v1/ml/dataset/stream",
    headers={"Content-Type": "application/x-ndjson"},
    data=data.encode('utf-8'),
    timeout=30
)

print(f"\n📥 Status: {response.status_code}")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))


# python scripts/send_final.py