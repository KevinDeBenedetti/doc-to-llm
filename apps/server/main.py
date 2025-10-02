from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.core.logger import setup_logging
from src.routes import openai, translate, format

from src.core import database

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.create_db_and_tables()
    yield


app = FastAPI(
    title="Doc To Llm",
    description="A FastAPI application for document translation and language model interaction.",
    version="0.0.1",
    lifespan=lifespan,
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
