import asyncio
from services.riksdag_api import fetch_paginated
from cleaners.clean_dokument import clean_dokument
from services.kafka_producer import send_to_kafka

INTERVAL = 1800
PAGES = 5

async def main():
    while True:
        print(" Hämtar dokument (5 sidor)...")
        raw = await fetch_paginated("dokument", pages=PAGES)
        cleaned = clean_dokument(raw)
        send_to_kafka("dokument_topic", cleaned)
        print(f" Dokument klar! {len(cleaned)} poster skickade. Väntar 30 min...")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
