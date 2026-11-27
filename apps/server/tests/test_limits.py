import pytest

from src.core.config import settings
from tests.test_routes import md_file

RAW = {"enhance": "false", "clean": "false"}


@pytest.fixture
def small_limits(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 1000)
    monkeypatch.setattr(settings, "max_content_chars", 600)


def test_upload_at_the_byte_limit_is_accepted(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 1000)

    response = client.post(
        "/format/doc/markdown", params=RAW, files=md_file("x" * 1000)
    )

    assert response.status_code == 200
    assert response.text == "x" * 1000


def test_upload_above_the_byte_limit_gets_413(client, small_limits):
    response = client.post(
        "/format/doc/markdown", params=RAW, files=md_file("x" * 1001)
    )

    assert response.status_code == 413


def test_upload_above_the_char_limit_gets_413(client, monkeypatch):
    monkeypatch.setattr(settings, "max_content_chars", 600)

    response = client.post("/format/doc/markdown", params=RAW, files=md_file("é" * 601))

    assert response.status_code == 413


def test_translate_upload_above_the_byte_limit_gets_413(client, small_limits):
    data = {"source_language": "en", "target_language": "fr"}

    response = client.post("/translate-file", files=md_file("x" * 1001), data=data)

    assert response.status_code == 413


@pytest.mark.parametrize("path", ["/format/doc/text", "/format/doc/text/markdown"])
def test_json_content_at_the_char_limit_is_accepted(client, small_limits, path):
    body = {"content": "x" * 600, "enhance": False, "clean": False}

    assert client.post(path, json=body).status_code == 200


@pytest.mark.parametrize(
    "path", ["/format/doc/text", "/format/doc/text/markdown", "/format/doc/text/stream"]
)
def test_json_content_above_the_char_limit_gets_422(client, ai, small_limits, path):
    body = {"content": "x" * 601, "enhance": True, "clean": False}

    response = client.post(path, json=body)

    assert response.status_code == 422
    assert ai.prompts == []


def test_limits_are_read_from_the_environment(monkeypatch):
    from src.core.config import Settings

    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2048")
    monkeypatch.setenv("MAX_CONTENT_CHARS", "1024")

    configured = Settings()

    assert (configured.max_upload_bytes, configured.max_content_chars) == (2048, 1024)
