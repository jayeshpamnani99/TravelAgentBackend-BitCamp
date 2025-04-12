import httpx
from app.config import settings

FSQ_API = "https://api.foursquare.com/v3/places/search"
HEADERS = {
    "Authorization": settings.FOURSQUARE_API_KEY
}

async def get_places(city: str, category: str, limit: int = 5) -> list:
    params = {
        "query": category,
        "near": city,
        "limit": limit,
        "sort": "RELEVANCE"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FSQ_API, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            {
                "name": p["name"],
                "address": p["location"].get("formatted_address", "N/A"),
                "categories": [c["name"] for c in p.get("categories", [])]
            }
            for p in data.get("results", [])
        ]
