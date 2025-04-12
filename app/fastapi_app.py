from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI(title="Agentverse 2.0")

app.include_router(api_router, prefix="/api/v1")
