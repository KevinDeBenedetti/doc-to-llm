from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from src.core.config import settings
from src.core.cors import add_cors
from src.core.logger import setup_logging
from src.core.security import require_api_key
from src.routes import openai, translate, format

setup_logging(log_file=settings.log_file)

app = FastAPI(
    title="doc-to-llm",
    description="A FastAPI application for document translation and language model interaction.",
    version="0.0.1",
)

add_cors(app, settings.cors_origins)

# Every route that reaches the LLM requires a key from API_KEYS.
protected = [Depends(require_api_key)]
app.include_router(
    openai.router, prefix="/openai", tags=["OpenAI"], dependencies=protected
)
app.include_router(translate.router, tags=["Translation"], dependencies=protected)
app.include_router(
    format.router, prefix="/format", tags=["Format"], dependencies=protected
)


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs", status_code=302)


@app.get("/healthz", summary="Liveness check", tags=["Health"])
def healthz():
    """Answer without a key and without calling the LLM."""
    return {"status": "ok"}
