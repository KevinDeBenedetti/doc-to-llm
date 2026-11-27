import asyncio

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

import main
from src.core.config import settings
from src.services import translate
from src.services.translate import TranslateService
from tests.conftest import API_KEY


class FakeChatModel:
    """Stands in for the chat model: no network, upper-cases each chunk.

    A chunk containing "CUT" comes back as if the token limit had stopped it.
    """

    def __init__(self):
        self.chunks = []
        self.models = []

    def build(self, model, temperature):
        self.models.append(model)
        return RunnableLambda(self.reply)

    def reply(self, prompt):
        chunk = prompt.to_messages()[-1].content.split("Content:\n", 1)[1].rstrip()
        self.chunks.append(chunk)
        if "CUT" in chunk:
            return AIMessage(
                content=chunk[:10].upper(),
                response_metadata={"finish_reason": "length"},
            )
        return AIMessage(
            content=chunk.upper(), response_metadata={"finish_reason": "stop"}
        )


@pytest.fixture
def llm(monkeypatch):
    model = FakeChatModel()
    monkeypatch.setattr(translate, "build_chat_model", model.build)
    return model


@pytest.fixture
def client(llm):
    return TestClient(main.app, headers={"X-API-Key": API_KEY})


def run_translation(content):
    return asyncio.run(
        TranslateService().translate_markdown(
            content=content, source_language="fr", target_language="en"
        )
    )


def test_long_document_is_translated_chunk_by_chunk(llm):
    words = [f"w{i}" for i in range(1500)]
    content = "\n\n".join(" ".join(words[i : i + 20]) for i in range(0, 1500, 20))

    result = run_translation(content)

    assert len(llm.chunks) > 1
    assert result.content.split() == [word.upper() for word in words]
    assert result.warnings == []


def test_truncated_reply_keeps_the_source_chunk_and_warns(llm):
    content = "# One\n\n" + "one " * 500 + "\n\n# Two\n\n" + "two CUT " * 200

    result = run_translation(content)

    assert len(llm.chunks) == 2
    assert "ONE ONE" in result.content
    assert ("two CUT " * 200).strip() in result.content
    assert len(result.warnings) == 1
    assert "2/2" in result.warnings[0]


def upload(content="Bonjour"):
    return {"file": ("doc.md", content.encode(), "text/markdown")}


def test_translate_file_returns_translation(client):
    data = {"source_language": "fr", "target_language": "en", "model_name": "m"}

    response = client.post("/translate-file", files=upload(), data=data)

    assert response.status_code == 200
    assert response.json() == {
        "translated_content": "BONJOUR",
        "source_language": "fr",
        "target_language": "en",
        "model_used": "m",
        "warnings": [],
    }


def test_translate_file_reports_truncated_chunks(client):
    data = {"source_language": "fr", "target_language": "en", "model_name": "m"}

    response = client.post("/translate-file", files=upload("Bonjour CUT"), data=data)

    assert response.status_code == 200
    assert response.json()["translated_content"] == "Bonjour CUT"
    assert len(response.json()["warnings"]) == 1


def test_translate_file_defaults_to_the_configured_model(client, llm, monkeypatch):
    monkeypatch.setattr(settings, "openai_model", "configured-model")
    data = {"source_language": "fr", "target_language": "en"}

    response = client.post("/translate-file", files=upload(), data=data)

    assert response.status_code == 200
    assert response.json()["model_used"] == "configured-model"
    assert llm.models == ["configured-model"]


def test_translate_file_without_any_model_is_rejected(client, llm, monkeypatch):
    monkeypatch.setattr(settings, "openai_model", None)
    data = {"source_language": "fr", "target_language": "en"}

    response = client.post("/translate-file", files=upload(), data=data)

    assert response.status_code == 400
    assert llm.models == []


def test_chat_model_uses_the_configured_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "openai_base_url", "http://llm.example.test/v1")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    model = translate.build_chat_model("m", 0.6)

    assert model.openai_api_base == "http://llm.example.test/v1"
    assert model.model_name == "m"
