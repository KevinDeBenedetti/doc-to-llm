from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.core.logger import setup_logging
from src.routes import openai, translate, format

setup_logging()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openai.router)
app.include_router(translate.router)
app.include_router(format.router)


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs", status_code=302)
