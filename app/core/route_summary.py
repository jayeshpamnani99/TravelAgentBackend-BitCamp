import google.generativeai as genai
from app.config import settings
from app.prompts.utils import get_prompt

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

async def get_route_summary(source: str, destination: str) -> str:
    prompt_template = get_prompt("route_summary.txt")
    
    final_prompt = prompt_template.format(
        source=source,
        destination=destination
    )
    response = model.generate_content(final_prompt)
    return response.text.strip()
