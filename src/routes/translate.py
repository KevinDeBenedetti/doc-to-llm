import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from src.services.translate import TranslateService
from src.schemas import TranslationRequest, TranslationResponse

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/translate-file", response_model=TranslationResponse)
async def translate_file(
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
    model_name: str = Form(...),
):
    try:
        content = await file.read()
        logger.info(f"File content: {content[:100]}")
        content_str = content.decode("utf-8")

        translation_req = TranslationRequest(
            content=content_str,
            source_language=source_language,
            target_language=target_language,
            model_name=model_name,
        )

        translate_service = TranslateService(model_name=translation_req.model_name)
        translated_text = await translate_service.translate_markdown(
            content=translation_req.content,
            source_language=translation_req.source_language,
            target_language=translation_req.target_language,
            model_name=translation_req.model_name,
        )

        return TranslationResponse(
            translated_content=translated_text,
            source_language=translation_req.source_language,
            target_language=translation_req.target_language,
            model_used=translation_req.model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating file: {str(e)}")
