import datetime
from datetime import datetime, timedelta
import httpx
from app.config import settings

FORECAST_API_URL = "http://api.weatherapi.com/v1/forecast.json"
HISTORICAL_API_URL = "http://api.weatherapi.com/v1/history.json"

async def get_weather(city: str, start_date: str, end_date: str) -> dict:
    today = datetime.today().date()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # If both start and end dates are within 14 days from today, fetch forecast
    if (start - today).days <= 14 and (end - today).days <= 14:
        return await fetch_forecast(city, start, end)
    
    # If either start or end date is beyond 14 days, fetch historical data
    try:
        return await fetch_historical(city, start, end)
    except Exception:
        return {
            "city": city,
            "message": "Weather forecast is only available 14 days in advance. We'll update this closer to your trip."
        }

async def fetch_forecast(city: str, start: datetime.date, end: datetime.date) -> dict:
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": city,
        "days": 14,
        "aqi": "no",
        "alerts": "no"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        forecast_days = data.get("forecast", {}).get("forecastday", [])
        forecast_map = {}

        for day in forecast_days:
            forecast_date = datetime.strptime(day["date"], "%Y-%m-%d").date()  # Ensure forecast_date is a date object
            if start <= forecast_date <= end:
                forecast_map[day["date"]] = {
                    "avg_temp_c": day["day"]["avgtemp_c"],
                    "condition": day["day"]["condition"]["text"],
                    "max_wind_kph": day["day"]["maxwind_kph"],
                    "humidity": day["day"]["avghumidity"]
                }

        return {
            "city": city,
            "type": "forecast",
            "forecast": forecast_map
        }

async def fetch_historical(city: str, start: datetime.date, end: datetime.date) -> dict:
    historic_start = start.replace(year=start.year - 1)
    historic_end = end.replace(year=end.year - 1)

    results = {}
    async with httpx.AsyncClient() as client:
        current_date = historic_start
        while current_date <= historic_end:
            params = {
                "key": settings.WEATHER_API_KEY,
                "q": city,
                "dt": current_date.strftime("%Y-%m-%d")
            }
            response = await client.get(HISTORICAL_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            day = data.get("forecast", {}).get("forecastday", [])[0]["day"]
            try:
                results[current_date.strftime("%Y-%m-%d")] = {
                    "avg_temp_c": day["avgtemp_c"],
                    "condition": day["condition"]["text"],
                    "max_wind_kph": day["maxwind_kph"],
                    "humidity": day["avghumidity"]
                }
            except KeyError:
                results[current_date.strftime("%Y-%m-%d")] = {
                    "avg_temp_c": None,
                    "condition": "No data",
                    "max_wind_kph": None,
                    "humidity": None
                }
            current_date += datetime.timedelta(days=1)

    return {
        "city": city,
        "type": "historical",
        "note": "Historical weather from the same time last year (for reference)",
        "forecast": results
    }