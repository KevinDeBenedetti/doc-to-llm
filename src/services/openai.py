from openai import AsyncOpenAI
from typing import List, Dict
from src.utils.config import config

class OpenAIService:
    def __init__(self):
        self.config = config
        self.ai_provider = self.config.ai_provider.lower()
        self.api_key = self.config.openai_api_key
        self.base_url = self.config.openai_base_url
        self.model = self.config.model_config
        
        # Initialize OpenAI client with new v1.0+ API
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def health_check(self) -> Dict[str, any]:
        """
        Health check OpenAI service
        Returns status and connection information
        """
        try:
            # Test API connection by listing models
            response = await self.client.models.list()
            return {
                "status": "healthy",
                "provider": self.ai_provider,
                "model": self.model,
                "base_url": self.base_url,
                "models_available": len(response.data) if response.data else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.ai_provider,
                "error": str(e),
                "base_url": self.base_url
            }

    async def get_models(self) -> List[Dict[str, any]]:
        """
        Get available OpenAI models
        Returns list of available models with their information
        """
        try:
            response = await self.client.models.list()
            models = []
            
            for model in response.data:
                models.append({
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": model.owned_by
                })
            
            return models
            
        except Exception as e:
            raise Exception(f"Failed to retrieve models: {str(e)}")

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, any]:
        """
        Create a chat completion using OpenAI API
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.model_dump()
        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    async def text_completion(self, prompt: str, **kwargs) -> Dict[str, any]:
        """
        Create a text completion using OpenAI API
        """
        try:
            response = await self.client.completions.create(
                model=self.model,
                prompt=prompt,
                **kwargs
            )
            return response.model_dump()
        except Exception as e:
            raise Exception(f"Text completion failed: {str(e)}")

