import httpx
from app.config import settings

FSQ_SEARCH_URL = "https://api.foursquare.com/v3/places/search"
FSQ_PHOTO_URL = "https://api.foursquare.com/v3/places/{fsq_id}/photos"
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
        response = await client.get(FSQ_SEARCH_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        places = []
        for place in data.get("results", []):
            fsq_id = place.get("fsq_id")
            photo_url = await get_place_photo(client, fsq_id)

            places.append({
                "name": place["name"],
                "address": place["location"].get("formatted_address", "N/A"),
                "categories": [c["name"] for c in place.get("categories", [])],
                "latitude": place["geocodes"]["main"]["latitude"],
                "longitude": place["geocodes"]["main"]["longitude"],
                "photo_url": photo_url
            })

        return places

async def get_place_photo(client: httpx.AsyncClient, fsq_id: str) -> str:
    url = FSQ_PHOTO_URL.format(fsq_id=fsq_id)
    response = await client.get(url, headers=HEADERS)
    if response.status_code == 200:
        photos = response.json()
        if photos:
            photo = photos[0]  # Use the first photo
            return f"{photo['prefix']}original{photo['suffix']}"
    return ""
