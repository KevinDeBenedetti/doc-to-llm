import json


from src.routes import format as format_routes


def md_file(content="# Title\n\nBody", name="doc.md"):
    return {"file": (name, content.encode(), "text/markdown")}


def test_root_redirects_to_docs(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/docs"


def test_openai_health(client):
    assert client.get("/openai/health").json()["status"] == "healthy"


def test_openai_models(client):
    assert client.get("/openai/models").json() == [{"id": "test-model"}]


def test_format_doc_cleans_and_enhances(client):
    response = client.post("/format/doc", files=md_file())

    assert response.status_code == 200
    body = response.json()
    assert "LASTUPDATED: TRUE" in body["formatted_content"]
    assert body["sections"] == ["TITLE"]
    assert body["warnings"] == []


def test_format_doc_text_without_enhance_skips_ai(client, ai):
    response = client.post(
        "/format/doc/text", json={"content": "# Title", "enhance": False}
    )

    assert response.status_code == 200
    assert ai.prompts == []
    assert "[[toc]]" in response.json()["formatted_content"]


def test_format_doc_rejects_non_markdown_with_400(client):
    response = client.post("/format/doc", files=md_file(name="doc.txt"))

    assert response.status_code == 400


def test_format_doc_rejects_non_utf8_with_400(client):
    files = {"file": ("doc.md", "é".encode("latin-1"), "text/markdown")}

    assert client.post("/format/doc", files=files).status_code == 400


def test_translate_rejects_non_utf8_with_400(client):
    files = {"file": ("doc.md", b"\xff\xfe\xfa", "text/markdown")}
    data = {"source_language": "fr", "target_language": "en", "model_name": "m"}

    assert client.post("/translate-file", files=files, data=data).status_code == 400


def test_format_doc_markdown_returns_raw_content(client):
    response = client.post(
        "/format/doc/markdown", files=md_file(), params={"enhance": False}
    )

    assert response.status_code == 200
    assert response.text.startswith("---\noutline: deep")
    assert response.headers["x-format-warnings"] == "0"


def test_format_doc_text_markdown_returns_raw_content(client):
    response = client.post(
        "/format/doc/text/markdown", json={"content": "Body", "clean": False}
    )

    assert response.text == "BODY"


def stream_events(response):
    return [json.loads(line) for line in response.text.splitlines()]


def test_streaming_and_plain_endpoints_return_the_same_content(client):
    content = "# Title\n\n" + "\n\n".join(
        f"## Part {i}\n\n" + "x " * 400 for i in range(8)
    )
    plain = client.post("/format/doc/text", json={"content": content}).json()

    stream = client.post("/format/doc/stream", files=md_file(content))
    events = stream_events(stream)

    assert events[-1]["status"] == "completed"
    assert events[-1]["result"]["formatted_content"] == plain["formatted_content"]
    assert [e["status"] for e in events].count("ai_processing") > 1


def test_long_document_is_not_duplicated_at_chunk_boundaries(client, ai):
    words = [f"w{i}" for i in range(1500)]
    content = "\n\n".join(" ".join(words[i : i + 20]) for i in range(0, 1500, 20))

    response = client.post(
        "/format/doc/text/markdown", json={"content": content, "clean": False}
    )

    assert len(ai.prompts) > 1
    assert response.text.split() == [word.upper() for word in words]
    assert ai.health_checks == 1


def test_truncated_ai_reply_is_reported_and_original_kept(client, ai):
    ai.finish_reason = "length"

    body = client.post(
        "/format/doc/text", json={"content": "Body", "clean": False}
    ).json()

    assert body["formatted_content"] == "Body"
    assert len(body["warnings"]) == 1


def test_unhealthy_ai_is_skipped_with_a_warning(client, ai):
    ai.healthy = False

    events = stream_events(
        client.post("/format/doc/text/stream", json={"content": "Body", "clean": False})
    )

    assert "ai_skipped" in [e["status"] for e in events]
    assert events[-1]["result"]["formatted_content"] == "Body"
    assert events[-1]["result"]["warnings"]


def test_markdown_route_accepts_non_latin1_filename(client):
    response = client.post(
        "/format/doc/markdown",
        files=md_file(name="指南 v1;x.md"),
        params={"enhance": False},
    )

    assert response.status_code == 200
    assert "filename*=UTF-8''" in response.headers["content-disposition"]


def test_failures_do_not_expose_exception_text(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    async def boom_stream(*args, **kwargs):
        raise RuntimeError("secret internal detail")
        yield

    monkeypatch.setattr(format_routes, "format_document", boom)
    monkeypatch.setattr(format_routes, "iter_format_document", boom_stream)

    plain = client.post("/format/doc/text", json={"content": "x"})
    stream = client.post("/format/doc/text/stream", json={"content": "x"})

    assert plain.status_code == 500
    assert "secret" not in plain.text
    assert stream_events(stream)[-1]["status"] == "error"
    assert "secret" not in stream.text
