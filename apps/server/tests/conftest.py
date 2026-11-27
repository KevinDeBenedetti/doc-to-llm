import os

import pytest

# Settings require an API key at import time; tests never reach the network.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "test-model")
os.environ.setdefault("API_KEYS", "test-api-key,second-api-key")

# The key the test clients send in X-API-Key.
API_KEY = "test-api-key"


class FakeAIService:
    """Stands in for OpenAIService: no network, records every prompt."""

    def __init__(self, healthy=True, finish_reason="stop"):
        self.healthy = healthy
        self.finish_reason = finish_reason
        self.prompts = []
        self.health_checks = 0

    async def health_check(self):
        self.health_checks += 1
        if self.healthy:
            return {"status": "healthy", "model": "test-model", "models_available": 1}
        return {"status": "unhealthy", "error": "down"}

    async def get_models(self):
        return [{"id": "test-model"}]

    async def chat_completion(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        self.prompts.append(prompt)
        chunk = prompt.split("\n\n", 1)[1].rsplit("\n\nInstructions", 1)[0]
        return {
            "choices": [
                {
                    "finish_reason": self.finish_reason,
                    "message": {"content": chunk.upper()},
                }
            ]
        }


@pytest.fixture
def ai(monkeypatch):
    # Imported here: the app modules read Settings, which needs the env above.
    from src.routes import openai as openai_routes
    from src.services import vitepress

    service = FakeAIService()
    monkeypatch.setattr(vitepress, "get_openai_service", lambda: service)
    monkeypatch.setattr(openai_routes, "OpenAIService", lambda: service)
    return service


@pytest.fixture
def client(ai):
    """A client of the app that sends a valid API key, with the LLM faked."""
    from fastapi.testclient import TestClient

    import main

    return TestClient(main.app, headers={"X-API-Key": API_KEY})
