import logging

from fastapi import APIRouter, Depends, Form, HTTPException

from src.routes.uploads import TextUpload, read_text_upload
from src.schemas.translate import TranslateRequest, TranslateResponse
from src.services.translate import TranslateService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/translate-file", response_model=TranslateResponse)
async def translate_file(
    upload: TextUpload = Depends(read_text_upload),
    source_language: str = Form(...),
    target_language: str = Form(...),
    model_name: str | None = Form(
        None, description="Model to use; defaults to OPENAI_MODEL"
    ),
):
    translation_req = TranslateRequest(
        content=upload.content,
        source_language=source_language,
        target_language=target_language,
        model_name=model_name,
    )
    translate_service = TranslateService(model_name=translation_req.model_name)
    if not translate_service.model_name:
        raise HTTPException(
            status_code=400,
            detail="model_name is required when OPENAI_MODEL is not set",
        )

    logger.info("Translating %s (%d characters)", upload.filename, len(upload.content))
    try:
        result = await translate_service.translate_markdown(
            content=translation_req.content,
            source_language=translation_req.source_language,
            target_language=translation_req.target_language,
        )
    except Exception as e:
        logger.exception("Translation failed")
        raise HTTPException(status_code=500, detail="Error translating file") from e

    return TranslateResponse(
        translated_content=result.content,
        source_language=translation_req.source_language,
        target_language=translation_req.target_language,
        model_used=translate_service.model_name,
        warnings=result.warnings,
    )
