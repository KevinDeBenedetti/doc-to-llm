from typing import Optional, List, Any
# from langchain_openai import ChatOpenAI
from openai.types import Model
from datetime import datetime, timedelta

from src.shared.config import config

class AIService:
    _models_cache = None    
    _cache_timestamp = None
    _cache_duration = timedelta(minutes=30)

    def __init__(self, custom_model: Optional[str] = None):
        self.settings = config()
        self.ai_provider = self.settings.ai_provider.lower()
        self.model = custom_model or getattr(self.settings, "openai_model", None)

        self._providers = {
            "openai": self._init_openai,
            # "ollama": self._init_ollama,  # example future extension
        }
        try:
            self._providers[self.ai_provider]()
        except KeyError:
            raise ValueError(f"Unsupported AI provider: {self.ai_provider}")

    def _init_openai(self):
        api_key = self.settings.openai_api_key
        self.base_url = self.settings.openai_api_base
        if not api_key:
            raise ValueError("Missing OpenAI API key (openai_api_key).")
        self.client = OpenAI(api_key=api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=api_key)
        if not self.model:
            self.model = "gpt-oss"

    # def _init_ollama(self):
    #     # Placeholder for future provider implementation
    #     pass

    async def chat(self, messages: List[dict], **params) -> Any:
        if not hasattr(self, "client"):
            raise ValueError("AI Client not initialized.")
        model = params.pop("model", None) or self.model
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **{k: v for k, v in params.items() if v is not None}
        )
        return response

    async def healthcheck(self):
        try:
            if not hasattr(self, "client"):
                return {"status": "error", "message": "AI client not initialized."}
            if not self.model:
                return {"status": "error", "message": "No model configured."}

            # Test API connectivity with a simple completion request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0
            )

            if response and getattr(response, "choices", None) and len(response.choices) > 0:
                # Verify we got a valid response
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    details = f"provider={self.ai_provider}, model={self.model}"
                    if getattr(self, "base_url", None):
                        details += f", base_url={self.base_url}"
                    
                    # Additional API info
                    api_info = {
                        "status": "ok", 
                        "message": f"AI service operational ({details}).",
                        "model_used": self.model,
                        "provider": self.ai_provider,
                        "response_id": getattr(response, "id", None),
                        "usage": getattr(response, "usage", None)
                    }
                    
                    if getattr(self, "base_url", None):
                        api_info["base_url"] = self.base_url
                        
                    return api_info
                    
            return {"status": "error", "message": "Invalid API response structure."}
            
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error information
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"status": "error", "message": "Authentication failed - check API key."}
            elif "404" in error_msg or "not found" in error_msg.lower():
                return {"status": "error", "message": f"Model '{self.model}' not found or not accessible."}
            elif "rate limit" in error_msg.lower():
                return {"status": "error", "message": "Rate limit exceeded."}
            elif "timeout" in error_msg.lower():
                return {"status": "error", "message": "API request timeout."}
            else:
                return {"status": "error", "message": f"Health check failed: {error_msg}"}


    async def list_models(self, use_cache: bool = True) -> list[Model]:
        try:
            if not hasattr(self, "client"):
                return []
            response = self.client.models.list()

            # Verify cache
            if (use_cache and 
                AIService._models_cache is not None and 
                AIService._cache_timestamp is not None and
                datetime.now() - AIService._cache_timestamp < AIService._cache_duration):
                return AIService._models_cache

            # Fetch models from API
            response = self.client.models.list()
            AIService._models_cache = response.data
            AIService._cache_timestamp = datetime.now()

            return response.data
        except Exception as e:
            print("Error while fetching models:", e)
            return []
