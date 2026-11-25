import json
import logging
from collections.abc import AsyncGenerator
from dataclasses import asdict
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from src.routes.uploads import TextUpload, read_markdown_upload
from src.schemas.format import DocumentRequest, DocumentResponse
from src.services.vitepress import FormatResult, format_document, iter_format_document

router = APIRouter()

logger = logging.getLogger(__name__)


async def run_pipeline(content: str, clean: bool, enhance: bool) -> FormatResult:
    try:
        return await format_document(content, clean=clean, enhance=enhance)
    except Exception as e:
        logger.exception("Formatting failed")
        raise HTTPException(status_code=500, detail="Erreur lors du formatage") from e


def stream_pipeline(content: str, clean: bool, enhance: bool) -> StreamingResponse:
    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for event in iter_format_document(content, clean, enhance):
                yield json.dumps(event) + "\n"
        except Exception:
            # The response has started: report the failure as the last event.
            logger.exception("Streaming formatting failed")
            yield (
                json.dumps(
                    {
                        "status": "error",
                        "message": "Erreur lors du formatage streaming",
                    }
                )
                + "\n"
            )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def markdown_response(result: FormatResult, filename: str) -> Response:
    return Response(
        content=result.formatted_content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}",
            "X-Format-Warnings": str(len(result.warnings)),
        },
    )


@router.post(
    "/doc",
    response_model=DocumentResponse,
    summary="Format VitePress Markdown Documentation with AI",
    description="Nettoie et améliore la documentation markdown VitePress avec AI",
)
async def format_doc(
    upload: TextUpload = Depends(read_markdown_upload),
    enhance: bool = True,
    clean: bool = True,
):
    result = await run_pipeline(upload.content, clean, enhance)
    return DocumentResponse(**asdict(result))


@router.post(
    "/doc/text",
    response_model=DocumentResponse,
    summary="Format Markdown from Text Input with AI",
    description="Formate du contenu markdown fourni directement en texte avec AI",
)
async def format_doc_text(request: DocumentRequest):
    result = await run_pipeline(request.content, request.clean, request.enhance)
    return DocumentResponse(**asdict(result))


@router.post(
    "/doc/stream",
    summary="Format VitePress Markdown with AI Streaming",
    description="Formate la documentation markdown VitePress avec AI et streaming en temps réel",
)
async def format_doc_stream(
    upload: TextUpload = Depends(read_markdown_upload),
    enhance: bool = True,
    clean: bool = True,
):
    return stream_pipeline(upload.content, clean, enhance)


@router.post(
    "/doc/text/stream",
    summary="Format Markdown Text with AI Streaming",
    description="Formate du contenu markdown avec AI et streaming en temps réel",
)
async def format_doc_text_stream(request: DocumentRequest):
    return stream_pipeline(request.content, request.clean, request.enhance)


@router.post(
    "/doc/markdown",
    summary="Format VitePress Markdown - Content Only",
    description="Formate la documentation VitePress et renvoie uniquement le contenu markdown",
)
async def format_doc_markdown(
    upload: TextUpload = Depends(read_markdown_upload),
    enhance: bool = True,
    clean: bool = True,
):
    result = await run_pipeline(upload.content, clean, enhance)
    return markdown_response(result, upload.filename)


@router.post(
    "/doc/text/markdown",
    summary="Format Markdown Text - Content Only",
    description="Formate du contenu markdown et renvoie uniquement le contenu formaté",
)
async def format_doc_text_markdown(request: DocumentRequest):
    result = await run_pipeline(request.content, request.clean, request.enhance)
    return markdown_response(result, "formatted.md")
