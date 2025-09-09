# setup logging as early as possible
from src.utils.logger import setup_logging
setup_logging()

# main imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging

from src.utils.config import config

# routes
from src.routes.base import base
from src.routes import translate, translations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base)
app.include_router(translate.router)
app.include_router(translations.router)

@app.get("/", include_in_schema=False)
def root_redirect_to_docs():
    logging.info("Redirecting root to /docs")
    return RedirectResponse(url="/docs")