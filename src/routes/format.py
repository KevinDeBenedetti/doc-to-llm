from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse

from src.schemas.format import DocumentRequest, DocumentResponse
from src.services.openai import OpenAIService
from src.core.config import settings
from src.services.vitepress import (
    enhance_content_with_ai,
    extract_sections,
    format_vitepress_markdown,
    add_vitepress_utilities,
    process_document_streaming,
)

router = APIRouter()

openai_service = OpenAIService()


@router.post(
    "/doc",
    response_model=DocumentResponse,
    summary="Format VitePress Markdown Documentation with AI",
    description="Nettoie et améliore la documentation markdown VitePress avec AI",
)
async def format_doc(
    file: UploadFile = File(...), enhance: bool = True, clean: bool = True
):
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400, detail="Le fichier doit être un fichier markdown (.md)"
            )

        # Lire le contenu
        content = await file.read()
        content_str = content.decode("utf-8")

        # Formater le contenu VitePress
        if clean:
            content_str = format_vitepress_markdown(content_str)
            content_str = add_vitepress_utilities(content_str)

        # Améliorer avec AI
        if enhance:
            content_str = await enhance_content_with_ai(content_str)

        # Extraire les sections
        sections = extract_sections(content_str)

        # Compter les mots
        word_count = len(content_str.split())

        # Créer un résumé simple
        model_name = settings.openai_model or "AI"
        summary = f"Document formaté avec {model_name}: {len(sections)} sections et {word_count} mots"

        return DocumentResponse(
            formatted_content=content_str,
            summary=summary,
            word_count=word_count,
            sections=sections,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage : {str(e)}"
        )


@router.post(
    "/doc/text",
    response_model=DocumentResponse,
    summary="Format Markdown from Text Input with AI",
    description="Formate du contenu markdown fourni directement en texte avec AI",
)
async def format_doc_text(request: DocumentRequest):
    try:
        content = request.content

        # Formater le contenu VitePress
        if request.clean:
            content = format_vitepress_markdown(content)
            content = add_vitepress_utilities(content)

        # Améliorer avec AI
        if request.enhance:
            content = await enhance_content_with_ai(content)

        # Extraire les sections
        sections = extract_sections(content)

        # Compter les mots
        word_count = len(content.split())

        # Créer un résumé
        model_name = settings.openai_model or "AI"
        summary = f"Document formaté avec {model_name}: {len(sections)} sections et {word_count} mots"

        return DocumentResponse(
            formatted_content=content,
            summary=summary,
            word_count=word_count,
            sections=sections,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage : {str(e)}"
        )


@router.post(
    "/doc/stream",
    summary="Format VitePress Markdown with AI Streaming",
    description="Formate la documentation markdown VitePress avec AI et streaming en temps réel",
)
async def format_doc_stream(
    file: UploadFile = File(...), enhance: bool = True, clean: bool = True
):
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400, detail="Le fichier doit être un fichier markdown (.md)"
            )

        # Lire le contenu
        content = await file.read()
        content_str = content.decode("utf-8")

        # Créer le générateur de streaming
        async def generate():
            async for chunk in process_document_streaming(content_str, clean, enhance):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage streaming : {str(e)}"
        )


@router.post(
    "/doc/text/stream",
    summary="Format Markdown Text with AI Streaming",
    description="Formate du contenu markdown avec AI et streaming en temps réel",
)
async def format_doc_text_stream(request: DocumentRequest):
    try:
        # Créer le générateur de streaming
        async def generate():
            async for chunk in process_document_streaming(
                request.content, request.clean, request.enhance
            ):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage streaming : {str(e)}"
        )


@router.post(
    "/doc/markdown",
    summary="Format VitePress Markdown - Content Only",
    description="Formate la documentation VitePress et renvoie uniquement le contenu markdown",
)
async def format_doc_markdown(
    file: UploadFile = File(...), enhance: bool = True, clean: bool = True
):
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400, detail="Le fichier doit être un fichier markdown (.md)"
            )

        # Lire le contenu
        content = await file.read()
        content_str = content.decode("utf-8")

        # Formater le contenu VitePress
        if clean:
            content_str = format_vitepress_markdown(content_str)
            content_str = add_vitepress_utilities(content_str)

        # Améliorer avec AI
        if enhance:
            content_str = await enhance_content_with_ai(content_str)

        # Retourner le markdown comme texte brut
        return Response(
            content=content_str,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"inline; filename={file.filename}",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage : {str(e)}"
        )


@router.post(
    "/doc/text/markdown",
    summary="Format Markdown Text - Content Only",
    description="Formate du contenu markdown et renvoie uniquement le contenu formaté",
)
async def format_doc_text_markdown(request: DocumentRequest):
    try:
        content = request.content

        # Formater le contenu VitePress
        if request.clean:
            content = format_vitepress_markdown(content)
            content = add_vitepress_utilities(content)

        # Améliorer avec AI
        if request.enhance:
            content = await enhance_content_with_ai(content)

        # Retourner le markdown comme texte brut
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": "inline; filename=formatted.md",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage : {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du formatage : {str(e)}"
        )
