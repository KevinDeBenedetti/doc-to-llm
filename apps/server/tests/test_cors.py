import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from src.core.config import Settings
from src.core.cors import add_cors

ALLOWED = "https://docs.example.com"
PREFLIGHT = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type,x-api-key",
}


def app_with_cors(origins):
    app = FastAPI()
    add_cors(app, origins)

    @app.post("/echo")
    def echo():
        return {}

    return TestClient(app)


def test_default_app_sends_no_cors_headers_to_any_origin():
    response = TestClient(main.app).options(
        "/format/doc/text", headers={"Origin": "https://evil.example", **PREFLIGHT}
    )

    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_preflight_from_an_unlisted_origin_gets_no_allow_origin():
    response = app_with_cors([ALLOWED]).options(
        "/echo", headers={"Origin": "https://evil.example", **PREFLIGHT}
    )

    assert "access-control-allow-origin" not in response.headers


def test_preflight_from_a_listed_origin_is_allowed_without_credentials():
    response = app_with_cors([ALLOWED]).options(
        "/echo", headers={"Origin": ALLOWED, **PREFLIGHT}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "access-control-allow-credentials" not in response.headers
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "x-api-key" in allowed_headers


def test_cors_origins_are_read_comma_separated(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", f" {ALLOWED} , https://app.example.com ,")

    assert Settings().cors_origins == [ALLOWED, "https://app.example.com"]


def test_wildcard_cors_origin_is_refused(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings()
