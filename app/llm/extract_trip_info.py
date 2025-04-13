from fastapi import HTTPException
import google.generativeai as genai
from app.config import settings
import re
import json
from typing import Dict, Optional
from datetime import datetime
import os

genai.configure(api_key=settings.GEMINI_API_KEY)

class ChatManager:
    def __init__(self):
        self.chats = {}  # trip_id -> chat session
        self.conversation_states = {}  # trip_id -> conversation state

    def get_or_create_chat(self, trip_id: str) -> tuple:
        if trip_id not in self.chats:
            # Create new chat and conversation state
            self.chats[trip_id] = genai.GenerativeModel("gemini-2.0-flash").start_chat(history=[])
            self.conversation_states[trip_id] = {
                "required_fields": ["origin", "destination", "start_date", "end_date"],
                "current_data": {
                    "origin": "",
                    "destination": "",
                    "start_date": "",
                    "end_date": "",
                    "follow_up": "",
                    "is_complete": False
                },
                "conversation_history": []
            }
        return self.chats[trip_id], self.conversation_states[trip_id]

    def close_chat(self, trip_id: str) -> None:
        if trip_id in self.chats:
            del self.chats[trip_id]
            del self.conversation_states[trip_id]

    def update_state(self, trip_id: str, new_data: Dict) -> None:
        if trip_id in self.conversation_states:
            state = self.conversation_states[trip_id]
            for field in state["required_fields"]:
                if field in new_data and new_data[field]:
                    state["current_data"][field] = new_data[field]
            
            state["current_data"]["follow_up"] = new_data.get("follow_up", "")
            state["current_data"]["is_complete"] = all(
                state["current_data"][field] for field in state["required_fields"]
            )

            # Close chat if conversation is complete
            if state["current_data"]["is_complete"]:
                self.close_chat(trip_id)

    def get_state(self, trip_id: str) -> Optional[Dict]:
        return self.conversation_states.get(trip_id, {}).get("current_data")

# Global chat manager
chat_manager = ChatManager()

prompt_file_path = os.path.join(os.path.dirname(__file__), "../prompts/initiating_prompt.txt")
with open(prompt_file_path, "r", encoding="utf-8") as file:
    initiating_prompt = file.read()

def extract_trip_info_from_prompt(prompt: str, trip_id: Optional[str] = None) -> dict:
    if not trip_id:
        trip_id = "default"  # For non-trip_id conversations
    
    # Get or create chat session and state
    chat, state = chat_manager.get_or_create_chat(trip_id)
    
    # Add current prompt to history
    state["conversation_history"].append(f"User: {prompt}")
    
    # Prepare the context for Gemini
    context = f"{initiating_prompt}\n\n"
    if state["conversation_history"]:
        context += "Previous conversation:\n" + "\n".join(state["conversation_history"][-3:]) + "\n\n"
    
    # Get response from Gemini
    response = chat.send_message(f"{context}Current user message: {prompt}")
    raw_text = response.text
    
    # Clean the response
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
    raw_text = re.sub(r"\s*```$", "", raw_text)
    
    try:
        # Parse the response
        response_data = json.loads(raw_text)
        
        # Update conversation state
        chat_manager.update_state(trip_id, response_data)
        
        # Add Gemini's response to history
        state["conversation_history"].append(f"Assistant: {response_data.get('follow_up', '')}")
        
        # Return current state
        return state["current_data"]
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response format from AI model")


