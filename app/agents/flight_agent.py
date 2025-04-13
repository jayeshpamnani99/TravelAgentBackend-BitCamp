import httpx
from app.config import settings
from datetime import datetime, timedelta
import json
from app.agents.airport_codes import get_airport_code

AMADEUS_API_URL = "https://test.api.amadeus.com/v2"
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"

def simplify_flight_data(flight_data: dict) -> dict:
    """Simplify the flight data to include only essential information."""
    simplified_flights = []
    
    for flight in flight_data.get("data", []):
        outbound = flight["itineraries"][0]["segments"][0]
        return_flight = flight["itineraries"][1]["segments"][-1]  # Get the last segment of return
        
        # Convert price to USD if needed
        price = flight["price"]
        if price["currency"] != "USD":
            # Note: In a real application, you would want to use a currency conversion API
            # For now, we'll just set it to USD and keep the same amount
            price["currency"] = "USD"
        
        simplified_flight = {
            "price": {
                "total": price["total"],
                "currency": "USD"  # Always set to USD
            },
            "outbound": {
                "departure": {
                    "airport": outbound["departure"]["iataCode"],
                    "time": outbound["departure"]["at"],
                    "terminal": outbound["departure"].get("terminal", "")
                },
                "arrival": {
                    "airport": outbound["arrival"]["iataCode"],
                    "time": outbound["arrival"]["at"],
                    "terminal": outbound["arrival"].get("terminal", "")
                },
                "duration": outbound["duration"],
                "airline": flight["validatingAirlineCodes"][0],
                "flight_number": outbound["number"]
            },
            "return": {
                "departure": {
                    "airport": return_flight["departure"]["iataCode"],
                    "time": return_flight["departure"]["at"],
                    "terminal": return_flight["departure"].get("terminal", "")
                },
                "arrival": {
                    "airport": return_flight["arrival"]["iataCode"],
                    "time": return_flight["arrival"]["at"],
                    "terminal": return_flight["arrival"].get("terminal", "")
                },
                "duration": return_flight["duration"],
                "airline": flight["validatingAirlineCodes"][0],
                "flight_number": return_flight["number"]
            }
        }
        simplified_flights.append(simplified_flight)
    
    return {
        "flights": simplified_flights,
        "total_offers": flight_data["meta"]["count"]
    }

async def get_flight_offers(origin: str, destination: str, departure_date: str, return_date: str) -> dict:
    # First get the access token
    token = await get_access_token()
    
    # Convert city names to airport codes
    origin_code = await get_airport_code(origin)
    destination_code = await get_airport_code(destination)
    
    # Check if dates are too far in the future
    today = datetime.now().date()
    departure = datetime.strptime(departure_date, "%Y-%m-%d").date()
    return_dt = datetime.strptime(return_date, "%Y-%m-%d").date()
    
    # Calculate months difference
    months_diff = (departure.year - today.year) * 12 + departure.month - today.month
    
    if months_diff > 11:
        return {
            "message": "Flight search is currently available for dates within the next 11 months.",
            "suggestion": "Please check back closer to your travel date for available flights.",
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "origin_code": origin_code,
            "destination_code": destination_code
        }
    
    # Search for flights
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "originLocationCode": origin_code,
        "destinationLocationCode": destination_code,
        "departureDate": departure_date,
        "returnDate": return_date,
        "adults": 1,
        "max": 5
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AMADEUS_API_URL}/shopping/flight-offers",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("data"):
                return {
                    "message": "No flights found for the selected dates.",
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "origin_code": origin_code,
                    "destination_code": destination_code
                }
            return simplify_flight_data(data)
        else:
            return {
                "error": "Failed to fetch flight offers",
                "status_code": response.status_code,
                "details": response.text
            }

async def get_access_token() -> str:
    params = {
        "grant_type": "client_credentials",
        "client_id": settings.AMADEUS_API_KEY,
        "client_secret": settings.AMADEUS_API_SECRET
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=params)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception("Failed to get access token from Amadeus API") 