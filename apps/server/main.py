from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.core.config import settings
from src.core.logger import setup_logging
from src.routes import openai, translate, format

setup_logging(log_file=settings.log_file)

app = FastAPI(
    title="doc-to-llm",
    description="A FastAPI application for document translation and language model interaction.",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openai.router, prefix="/openai", tags=["OpenAI"])
app.include_router(translate.router, tags=["Translation"])
app.include_router(format.router, prefix="/format", tags=["Format"])


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs", status_code=302)
