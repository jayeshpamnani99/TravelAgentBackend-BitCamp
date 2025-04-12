from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
    DEBUG = os.getenv("DEBUG", False)
    
settings = Settings()

