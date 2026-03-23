import httpx
from config.settings import RIKSDAGEN_APIS, HEADERS


async def fetch_data(source: str):
    if source not in RIKSDAGEN_APIS:
        raise ValueError("Ogiltig datakälla")
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        response = await client.get(RIKSDAGEN_APIS[source])
        response.raise_for_status()
        return response.json()


async def fetch_paginated(source: str, pages: int = 5):
    """Hämtar flera sidor från API:et och returnerar all data sammanslagen."""
    base_urls = {
        "voteringar": "https://data.riksdagen.se/voteringlista/?sz=500&utformat=json&p={}",
        "anforanden": "https://data.riksdagen.se/anforandelista/?sz=500&utformat=json&p={}",
        "dokument":   "https://data.riksdagen.se/dokumentlista/?sz=500&utformat=json&p={}",
    }

    if source not in base_urls:
        return await fetch_data(source)

    all_items = []
    async with httpx.AsyncClient(timeout=30.0, headers=HEADERS) as client:
        for page in range(1, pages + 1):
            try:
                url = base_urls[source].format(page)
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if source == "voteringar":
                    items = data.get("voteringlista", {}).get("votering", [])
                elif source == "anforanden":
                    items = data.get("anforandelista", {}).get("anforande", [])
                elif source == "dokument":
                    items = data.get("dokumentlista", {}).get("dokument", [])

                if isinstance(items, dict):
                    items = [items]
                if not items:
                    print(f"  Inga fler sidor efter sida {page}")
                    break

                all_items.extend(items)
                print(f"  Sida {page}: {len(items)} poster hämtade")

            except Exception as e:
                print(f"  Fel på sida {page}: {e}")
                break

    if source == "voteringar":
        return {"voteringlista": {"votering": all_items}}
    elif source == "anforanden":
        return {"anforandelista": {"anforande": all_items}}
    elif source == "dokument":
        return {"dokumentlista": {"dokument": all_items}}