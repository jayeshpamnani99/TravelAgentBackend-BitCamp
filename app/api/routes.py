from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.weather_agent import get_weather
from app.core.logic import generate_trip_plan
from app.llm.extract_trip_info import extract_trip_info_from_prompt
from app.agents.foursquare_agent import get_places

# from app.config import settings

router = APIRouter()

class TripRequest(BaseModel):
    destination: str
    days: int
    interests: list[str]

@router.post("/conversation")
def conversation(prompt: dict):
    # Extract trip info from prompt
    print("Prompt", prompt)
    trip_data = extract_trip_info_from_prompt(prompt['prompt'])
    print("Trip_data", trip_data)
    return trip_data
    
@router.post("/plan-trip")
def plan_trip(request: TripRequest):
    plan = generate_trip_plan(request.destination, request.days, request.interests)
    return {"itinerary": plan}

@router.get("/smart-weather")
async def weather_from_prompt():
    trip_data = {
        "destination": "Washington DC",
        "origin": "New York",
        "start_date": "2025-04-20",
        "end_date": "2025-04-25",
    }
    
    print("Trip_data", trip_data)
    
    # Get weather for both origin and destination
    origin_weather = await get_weather(trip_data["origin"], trip_data["start_date"], trip_data["end_date"])
    dest_weather = await get_weather(trip_data["destination"], trip_data["start_date"], trip_data["end_date"])
    print("Origin Weather:", origin_weather)
    print("Destination Weather:", dest_weather)

    return {
        "origin_weather": origin_weather,
        "destination_weather": dest_weather,
        "trip_dates": {
            "start": trip_data["start_date"],
            "end": trip_data["end_date"]
        }
    }

@router.get("/top-places")
async def top_places(city: str):
    try:
        places = await get_places(city, category="attractions")
        return {"city": city, "places_to_visit": places}
    except Exception as e:
        return {"error": str(e)}

@router.get("/restaurants")
async def restaurants(city: str):
    try:
        results = await get_places(city, category="restaurants")
        return {"city": city, "restaurants": results}
    except Exception as e:
        return {"error": str(e)}
