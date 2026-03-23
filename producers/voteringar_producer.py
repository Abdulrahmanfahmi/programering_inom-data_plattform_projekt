import asyncio
import httpx
from cleaners.clean_voteringar import clean_voteringar
from services.kafka_producer import send_to_kafka
from config.settings import HEADERS

INTERVAL = 1800
RIKSMOTEN = [None, "2025/26", "2024/25", "2023/24", "2022/23", "2021/22"]

async def fetch_riksmote(client, rm):
    if rm is None:
        url = "https://data.riksdagen.se/voteringlista/?sz=500&utformat=json"
    else:
        url = f"https://data.riksdagen.se/voteringlista/?sz=500&rm={rm.replace('/', '%2F')}&utformat=json"
    response = await client.get(url)
    response.raise_for_status()
    return response.json()

async def main():
    while True:
        print(" Hämtar voteringar — live + historisk...")
        async with httpx.AsyncClient(timeout=30.0, headers=HEADERS) as client:
            for rm in RIKSMOTEN:
                try:
                    raw = await fetch_riksmote(client, rm)
                    cleaned = clean_voteringar(raw)
                    send_to_kafka("voteringar_topic", cleaned)
                    label = "live" if rm is None else rm
                    print(f"  {label}: {len(cleaned)} röster skickade")
                except Exception as e:
                    label = "live" if rm is None else rm
                    print(f" {label}: {e}")
        print(" Voteringar klar! Väntar 30 min...")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())