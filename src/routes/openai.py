from fastapi import APIRouter

from src.services.openai import OpenAIService

router = APIRouter(
    prefix="/openai",
    tags=["OpenAI"]
)

@router.get(
    "/health",
    summary="Check OpenAI Service Health",
    description="Returns the health status of the OpenAI service to ensure it is operational."
)
async def get_openai_health():
    service = OpenAIService()
    return await service.health_check()

@router.get(
    "/models",
    summary="Get Available OpenAI Models",
    description="Returns a list of available OpenAI models that can be used for requests."
)
async def get_openai_models():
    service = OpenAIService()
    return await service.get_models()