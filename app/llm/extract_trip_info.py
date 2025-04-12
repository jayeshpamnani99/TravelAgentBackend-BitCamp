from fastapi import HTTPException
import google.generativeai as genai
from app.config import settings
import re
import json
from typing import Dict, Optional
from datetime import datetime
import os

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

prompt_file_path = os.path.join(os.path.dirname(__file__), "../prompts/initiating_prompt.txt")
with open(prompt_file_path, "r", encoding="utf-8") as file:
    initiating_prompt = file.read()

# Conversation state management
class ConversationState:
    def __init__(self):
        self.required_fields = ["origin", "destination", "start_date", "end_date"]
        self.current_data = {
            "origin": "",
            "destination": "",
            "start_date": "",
            "end_date": "",
            "follow_up": "",
            "is_complete": False
        }
        self.conversation_history = []

    def update_data(self, new_data: Dict) -> None:
        for field in self.required_fields:
            if field in new_data and new_data[field]:
                self.current_data[field] = new_data[field]
        
        self.current_data["follow_up"] = new_data.get("follow_up", "")
        self.current_data["is_complete"] = all(self.current_data[field] for field in self.required_fields)

    def get_current_state(self) -> Dict:
        return self.current_data

    def add_to_history(self, message: str) -> None:
        self.conversation_history.append(message)

# Global conversation state
conversation_state = ConversationState()

def extract_trip_info_from_prompt(prompt: str) -> dict:
    global conversation_state
    
    conversation_state.add_to_history(f"User: {prompt}")
    
    context = f"{initiating_prompt}\n\n"
    if conversation_state.conversation_history:
        context += "Previous conversation:\n" + "\n".join(conversation_state.conversation_history[-3:]) + "\n\n"
    
    response = chat.send_message(f"{context}Current user message: {prompt}")
    raw_text = response.text
    
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
    raw_text = re.sub(r"\s*```$", "", raw_text)
    
    try:
        response_data = json.loads(raw_text)
        conversation_state.update_data(response_data)
        conversation_state.add_to_history(f"Assistant: {response_data.get('follow_up', '')}")
        return conversation_state.get_current_state()
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response format from AI model")


