import httpx
from app.config import settings
import asyncio

FSQ_SEARCH_URL = "https://api.foursquare.com/v3/places/search"
FSQ_PHOTO_URL = "https://api.foursquare.com/v3/places/{fsq_id}/photos"
HEADERS = {
    "Authorization": settings.FOURSQUARE_API_KEY
}

async def get_places(city: str, category: str, limit: int = 5, max_retries: int = 3) -> list:
    params = {
        "query": category,
        "near": city,
        "limit": limit,
        "sort": "RELEVANCE"
    }

    retry_count = 0
    last_exception = None

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Set explicit timeout
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
                
        except httpx.ConnectTimeout as e:
            retry_count += 1
            last_exception = e
            if retry_count < max_retries:
                # Exponential backoff: wait 1s, then 2s, then 4s before retrying
                await asyncio.sleep(2 ** (retry_count - 1))
                continue
            raise Exception(f"Connection timeout after {max_retries} attempts") from e
            
        except httpx.TimeoutException as e:
            retry_count += 1
            last_exception = e
            if retry_count < max_retries:
                await asyncio.sleep(2 ** (retry_count - 1))
                continue
            raise Exception(f"Request timed out after {max_retries} attempts") from e
            
        except Exception as e:
            raise e

    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    
    # Fallback empty response if somehow we got here
    return []

async def get_place_photo(client: httpx.AsyncClient, fsq_id: str) -> str:
    try:
        url = FSQ_PHOTO_URL.format(fsq_id=fsq_id)
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            photos = response.json()
            if photos:
                photo = photos[0]  # Use the first photo
                return f"{photo['prefix']}original{photo['suffix']}"
    except Exception:
        # Silently handle photo fetch errors - photos are optional
        pass
    return ""