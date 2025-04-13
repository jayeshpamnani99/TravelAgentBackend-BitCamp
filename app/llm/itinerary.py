from datetime import datetime
import google.generativeai as genai
from app.prompts.utils import get_prompt
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

async def get_itinerary_response(source: str, destination: str, start_date: str, end_date: str) -> str:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    print("Source:", source)
    print("Destination:", destination)
    print("Start date:", start)
    print("End date:", end)
    
    # Load and fill prompt
    template = get_prompt("itinerary_prompt.txt")
    print("Template:", template)
    prompt = template.format(
        source=source,
        destination=destination,
        start_date=start.strftime("%B %d, %Y"),
        end_date=end.strftime("%B %d, %Y"),
    )
    print("Prompt:", prompt)
    response = model.generate_content(f"Current user message: {prompt}")
    raw_text = response.text
    print("Raw text:", raw_text)
    return raw_text.strip()  # Remove leading/trailing whitespace