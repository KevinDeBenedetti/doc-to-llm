import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from src.core.config import Settings
from tests.test_routes import md_file

PROTECTED = [
    ("get", "/openai/health", {}),
    ("get", "/openai/models", {}),
    ("post", "/format/doc", {"files": md_file()}),
    ("post", "/format/doc/text", {"json": {"content": "# Title"}}),
    ("post", "/format/doc/stream", {"files": md_file()}),
    ("post", "/format/doc/text/stream", {"json": {"content": "# Title"}}),
    ("post", "/format/doc/markdown", {"files": md_file()}),
    ("post", "/format/doc/text/markdown", {"json": {"content": "# Title"}}),
    (
        "post",
        "/translate-file",
        {
            "files": md_file(),
            "data": {"source_language": "en", "target_language": "fr"},
        },
    ),
]


@pytest.fixture
def anonymous(ai):
    return TestClient(main.app)


@pytest.mark.parametrize(("method", "path", "kwargs"), PROTECTED)
def test_protected_route_refuses_a_missing_key(anonymous, ai, method, path, kwargs):
    response = getattr(anonymous, method)(path, **kwargs)

    assert response.status_code == 401
    assert ai.prompts == [] and ai.health_checks == 0


@pytest.mark.parametrize(("method", "path", "kwargs"), PROTECTED)
def test_protected_route_refuses_a_wrong_key(anonymous, ai, method, path, kwargs):
    response = getattr(anonymous, method)(
        path, headers={"X-API-Key": "wrong-key"}, **kwargs
    )

    assert response.status_code == 401
    assert ai.prompts == [] and ai.health_checks == 0


def test_protected_route_accepts_any_configured_key(anonymous):
    for key in ("test-api-key", "second-api-key"):
        response = anonymous.get("/openai/health", headers={"X-API-Key": key})
        assert response.status_code == 200


def test_healthz_answers_without_a_key_or_an_llm_call(anonymous, ai):
    response = anonymous.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert ai.health_checks == 0


def test_api_keys_are_read_comma_separated(monkeypatch):
    monkeypatch.setenv("API_KEYS", " key-one , key-two ,")

    keys = [k.get_secret_value() for k in Settings().api_keys]

    assert keys == ["key-one", "key-two"]


def test_production_refuses_to_start_without_api_keys(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("API_KEYS", "")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-must-not-leak")

    with pytest.raises(ValidationError, match="API_KEYS") as error:
        Settings()

    assert "sk-must-not-leak" not in repr(error.value.errors())


def test_development_starts_without_api_keys(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("API_KEYS", "")

    assert Settings().api_keys == []


def test_non_ascii_key_is_refused_not_an_error(anonymous):
    response = anonymous.get(
        "/openai/health", headers={"X-API-Key": "clé-été".encode("latin-1")}
    )

    assert response.status_code == 401
