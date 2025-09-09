# setup logging as early as possible
from src.shared.logger import setup_logging
setup_logging()

# main imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging

from src.shared.config import config

# routes
from src.shared.api import base
from src.translator import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base)
app.include_router(router.router)

@app.get("/", include_in_schema=False)
def root_redirect_to_docs():
    logging.info("Redirecting root to /docs")
    return RedirectResponse(url="/docs")