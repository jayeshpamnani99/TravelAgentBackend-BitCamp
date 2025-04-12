from flask import json, jsonify
import google.generativeai as genai
from app.config import settings
import re

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")
import os

prompt_file_path = os.path.join(os.path.dirname(__file__), "../prompts/initiating_prompt.txt")
with open(prompt_file_path, "r", encoding="utf-8") as file:
    initiating_prompt = file.read()

def extract_trip_info_from_prompt(prompt: str) -> dict:
    system_prompt = f"{initiating_prompt}\n\nUser: {prompt}"

    response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
    raw_text = response.text
    # Clean the response if it's wrapped in ```json
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
    raw_text = re.sub(r"\s*```$", "", raw_text)

    # Use json.loads instead of eval for safety
    return raw_text
