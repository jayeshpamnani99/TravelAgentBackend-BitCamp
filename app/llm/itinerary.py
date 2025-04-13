from datetime import datetime
import google.generativeai as genai
from app.prompts.utils import get_prompt
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

async def get_itinerary_response(trip_data) -> str:
    start_date = trip_data['start_date']
    end_date = trip_data['end_date']
    source = trip_data['origin']
    destination = trip_data['destination']
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Load and fill prompt
    template = get_prompt("itinerary_prompt.txt")
    prompt = template.format(
        source=source,
        destination=destination,
        start_date=start.strftime("%B %d, %Y"),
        end_date=end.strftime("%B %d, %Y"),
    )
    response = model.generate_content(f"Current user message: {prompt}")
    raw_text = response.text
    return raw_text.strip()  # Remove leading/trailing whitespace