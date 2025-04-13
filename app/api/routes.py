from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.weather_agent import get_weather
from app.core.logic import generate_trip_plan
from app.llm.extract_trip_info import extract_trip_info_from_prompt, chat_manager
from app.agents.foursquare_agent import get_places
from app.core.trip_storage import trip_storage
from typing import Optional
from datetime import datetime
from app.core.trip_storage import TripStorage;
from app.llm.itinerary import get_itinerary_response
from app.core.route_summary import get_route_summary
from app.agents.flight_agent import get_flight_offers
import json

# from app.config import settings

router = APIRouter()

class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    trip_id: str

class TripInfoWrapper(BaseModel):
    trip_id: str

class ConversationRequest(BaseModel):
    prompt: str
    reset: bool = False
    trip_id: Optional[str] = None
    
class ItineraryRequest(BaseModel):
    source: str
    destination: str
    start_date: str
    end_date: str

class RouteRequest(BaseModel):
    source: str
    destination: str


@router.post("/conversation")
def conversation(request: ConversationRequest):
    if request.reset and request.trip_id:
        chat_manager.close_chat(request.trip_id)
        return {"message": "Conversation reset successfully"}
    
    # Extract trip info from prompt with trip_id
    trip_data = extract_trip_info_from_prompt(request.prompt, request.trip_id)
    
    # If we have a trip_id, handle storage
    if request.trip_id:
        existing_trip = trip_storage.get_trip(request.trip_id)
        if existing_trip:
            if not trip_storage.update_trip(request.trip_id, trip_data):
                raise HTTPException(status_code=500, detail="Failed to update trip")
        else:
            # Create new trip with the provided trip_id
            trip_storage.trip_data[request.trip_id] = {
                "data": trip_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            trip_storage._save_data()
        return {"trip_id": request.trip_id, **trip_data}
    
    # If trip is complete or user explicitly confirms completion
    if trip_data.get("is_complete", False) or "complete" in request.prompt.lower():
        trip_id = trip_storage.create_trip(trip_data)
        return {"trip_id": trip_id, **trip_data}
    
    return trip_data

@router.get("/trip/{trip_id}")
def get_trip(trip_id: str):
    trip = trip_storage.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.delete("/trip/{trip_id}")
def delete_trip(trip_id: str):
    if not trip_storage.delete_trip(trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": "Trip deleted successfully"}

@router.get("/trips")
def get_all_trips():
    return trip_storage.get_all_trips()

@router.post("/plan-trip")
def plan_trip(request: TripRequest):
    plan = generate_trip_plan(request.destination, request.days, request.interests)
    return {"itinerary": plan}

@router.post("/smart-weather")
async def weather_from_prompt(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get weather for both origin and destination
    origin_weather = await get_weather(trip_data["origin"], trip_data["start_date"], trip_data["end_date"])
    dest_weather = await get_weather(trip_data["destination"], trip_data["start_date"], trip_data["end_date"])

    return {
        "origin_weather": origin_weather,
        "destination_weather": dest_weather,
        "trip_dates": {
            "start": trip_data["start_date"],
            "end": trip_data["end_date"]
        }
    }

@router.post("/top-places")
async def top_places(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        city = trip_data["destination"]
        places = await get_places(city, category="attractions")
        return {"city": city, "places_to_visit": places}
    except Exception as e:
        return {"error": str(e)}

@router.post("/restaurants")
async def restaurants(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        city = trip_data["destination"]
        results = await get_places(city, category="restaurants")
        return {"city": city, "restaurants": results}
    except Exception as e:
        return {"error": str(e)}
    
@router.post("/route-summary")
async def route_summary(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        result = await get_route_summary(trip_data["origin"], trip_data["destination"])
        # result = get_route_summary(req.source, req.destination)
        return {"summary": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hotels")
async def hotels(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        city = trip_data["destination"]
        results = await get_places(city, category="hotels")
        return {"city": city, "hotels": results}
    except Exception as e:
        # More informative error handling
        error_type = type(e).__name__
        error_message = str(e) if str(e) else "Unknown error occurred while fetching hotel data"
        
        # Handle connection issues with a user-friendly message
        if "timeout" in error_message.lower() or "connect" in error_message.lower():
            return {
                "error": "Connection issue when trying to fetch hotel data. Please try again later.",
                "technical_details": f"{error_type}: {error_message}"
            }
        
        return {"error": f"{error_type}: {error_message}"}
    
@router.post("/itinerary")
async def itinerary(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    trip_data = get_trip(trip_id)['data']
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        itinerary_text = await get_itinerary_response(trip_data)
        return {"itinerary": itinerary_text}
    except Exception as e:
        return {"error": str(e)}

@router.post("/search-flights")
async def search_flights(TripInfoWrapper: TripInfoWrapper):
    trip_id = TripInfoWrapper.trip_id
    try:
        # Read trip data
        with open("trip_data.json", "r") as file:
            trips_data = json.load(file)
        
        # Check if trip_id exists in the data
        if trip_id not in trips_data:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Get the trip data
        trip = trips_data[trip_id]
        trip_info = trip["data"]
        
        # Validate required fields
        required_fields = ["origin", "destination", "start_date", "end_date"]
        for field in required_fields:
            if field not in trip_info:
                raise HTTPException(status_code=500, detail=f"Missing required field: {field}")
        
        # Get flight offers
        flight_offers = await get_flight_offers(
            origin=trip_info["origin"],
            destination=trip_info["destination"],
            departure_date=trip_info["start_date"],
            return_date=trip_info["end_date"]
        )
        
        return flight_offers
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON data in trip_data.json")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="trip_data.json file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))