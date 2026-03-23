import asyncio
from services.riksdag_api import fetch_data
from cleaners.clean_ledamoter import clean_ledamoter
from services.kafka_producer import send_to_kafka

INTERVAL = 1800  # 30 minuter

async def main():
    while True:
        print(" Hämtar ledamoter...")
        raw = await fetch_data("ledamoter")
        cleaned = clean_ledamoter(raw)
        send_to_kafka("ledamoter_topic", cleaned)
        print(f" Ledamoter klar! Väntar 30 min...")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())