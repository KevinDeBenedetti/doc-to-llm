from src.shared.logger import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs", status_code=302)