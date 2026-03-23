import asyncio
from services.riksdag_api import fetch_data
from cleaners.clean_kalender import clean_kalender
from services.kafka_producer import send_to_kafka

INTERVAL = 1800

async def main():
    while True:
        print(" Hämtar kalender...")
        raw = await fetch_data("kalender")
        cleaned = clean_kalender(raw)
        send_to_kafka("kalender_topic", cleaned)
        print(f" Kalender klar! Väntar 30 min...")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())