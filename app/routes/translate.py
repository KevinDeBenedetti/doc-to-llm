from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import PlainTextResponse
from enum import Enum

from app.services.ollama import translate_text, list_ollama_models

DEFAULT_MODEL = "gemma3"

class StaticOllamaModels(str, Enum):
    gemma3 = "gemma3:latest"
    gemma3_1b = "gemma3:1b"

router = APIRouter(
  prefix="/translate",
  tags=["translate"]
)

@router.post("/upload", response_class=PlainTextResponse)
async def translate_upload(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    model: StaticOllamaModels = Form(DEFAULT_MODEL)
):
    # Verify extension
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown files are supported")

    # Read the content
    content = (await file.read()).decode('utf-8')

    try:
        translated = translate_text(content, target_lang, model.value )
    except ConnectionError as ce:
        raise HTTPException(status_code=503, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")

    return translated
