from fastapi import APIRouter

from app.services.ai import AIService

base = APIRouter()

@base.get(
    "/health",
    summary="Check AI Service Health", 
    description="Returns the health status of the AI service to ensure it is operational."
)
async def get_ai_health():
    service = AIService()
    return await service.healthcheck()

@base.get(
    "/models", 
    summary="List Available AI Models", 
    description="Retrieves a list of all available AI models provided by the service."
)
async def get_ai_models():
    service = AIService()
    return await service.list_models()
