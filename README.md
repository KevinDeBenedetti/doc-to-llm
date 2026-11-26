# doc-to-llm

[![CI/CD](https://img.shields.io/github/actions/workflow/status/KevinDeBenedetti/doc-to-llm/ci.yaml?style=for-the-badge&label=CI%2FCD)](https://github.com/KevinDeBenedetti/doc-to-llm/actions/workflows/ci.yaml) [![License](https://img.shields.io/github/license/KevinDeBenedetti/doc-to-llm?style=for-the-badge)](LICENSE)

> A FastAPI service that cleans, enhances and translates VitePress Markdown documentation with an OpenAI-compatible LLM.

## Features

- Formats VitePress Markdown: frontmatter defaults, container titles, `.md` internal links, a table of contents
- Rewrites documentation with an LLM, chunk by chunk, and reports truncated replies as warnings
- Translates Markdown files between languages chunk by chunk, keeping their structure and reporting truncated replies as warnings
- Returns JSON, raw Markdown, or NDJSON progress events (`/stream` routes)
- Works with any OpenAI-compatible endpoint (`OPENAI_BASE_URL`)

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose, to run the service
- [uv](https://docs.astral.sh/uv/) and Python 3.13, to develop, lint and test locally
- An OpenAI-compatible API key and model

## Installation

```sh
cp .env.example .env
```

Fill in `.env`:

| Variable          | Required | Purpose                                                    |
| ----------------- | -------- | ---------------------------------------------------------- |
| `OPENAI_API_KEY`  | yes      | API key of the endpoint                                    |
| `OPENAI_BASE_URL` | no       | Endpoint URL; empty means `api.openai.com`                 |
| `OPENAI_MODEL`    | no       | Model for enhancement, and the default for translation     |
| `LOG_FILE`        | no       | Also log to this file, rotated at 10 MB (3 backups); logs always go to stdout |

## Usage

```sh
make start
```

The API listens on `http://localhost:8000`; its interactive OpenAPI docs are at `/docs`. Code edits under `apps/server` reload the server.

```sh
curl -F file=@guide.md "http://localhost:8000/format/doc/markdown?enhance=false"
```

| Route                         | Does                                              |
| ----------------------------- | ------------------------------------------------- |
| `POST /format/doc[/text]`     | Format a `.md` upload (or JSON `content`) to JSON |
| `POST /format/doc[/text]/markdown` | Same, returning raw Markdown                 |
| `POST /format/doc[/text]/stream`   | Same, streaming NDJSON progress events       |
| `POST /translate-file`        | Translate an uploaded file                        |
| `GET /openai/health`, `/openai/models` | Check the LLM endpoint                   |

## Development

```sh
make setup
make lint
make test
```

`make upgrade` updates `uv.lock` and the version floors in `apps/server/pyproject.toml`; `make help` lists every target. Pull requests run lint and tests in CI.

## License

MIT — see [LICENSE](LICENSE).
