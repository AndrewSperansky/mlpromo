# scripts/test_stream_fixed.py
import asyncio
import aiohttp
import json


async def test_stream():
    """Send NDJSON stream and read responses"""

    messages = [
        {"operation": "batch_start", "batch_id": "test-030", "total_count": 1},
        {"operation": "record", "data": {
            "SKU": "РН229840",
            "StoreID": "МГЗ №247",
            "Store_Location_Type": "Трассовый",
            "Date": "12.01.2026 00:00:00",
            "RegularPrice": 259.99,
            "PromoPrice": 229.99,
            "PercentPriceDrop": 11.54,
            "VolumeRegular": 119.86,
            "HistoricalSalesPromo": 442,
            "SalesQty_PrevModel": 0.25
        }},
        {"operation": "batch_end", "batch_id": "test-030"}
    ]

    # Важно: каждое сообщение отдельно с newline
    lines = [json.dumps(msg, ensure_ascii=False) + "\n" for msg in messages]

    print("📤 Sending NDJSON stream:")
    for line in lines:
        print(f"  {line.strip()}")

    # Создаем асинхронный генератор для отправки
    async def generate():
        for line in lines:
            print(f"📤 Sending: {line.strip()}")
            yield line.encode('utf-8')
            await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями

    async with aiohttp.ClientSession() as session:
        async with session.post(
                "http://localhost:8000/api/v1/ml/dataset/stream",
                headers={"Content-Type": "application/x-ndjson"},
                data=generate(),
                timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            print(f"\n📥 Response status: {response.status}")
            print("📥 Reading responses:\n")

            async for line in response.content:
                if line:
                    try:
                        msg = json.loads(line.decode('utf-8'))
                        print(json.dumps(msg, ensure_ascii=False, indent=2))
                        print("-" * 50)
                    except Exception as e:
                        print(f"Error parsing: {e}")
                        print(f"Raw: {line}")


if __name__ == "__main__":
    asyncio.run(test_stream())