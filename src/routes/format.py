from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain.text_splitter import MarkdownTextSplitter

# Utiliser le service OpenAI configuré
from src.services.openai import OpenAIService
from src.utils.config import config
import json
import asyncio
import re
from typing import Optional, AsyncGenerator

router = APIRouter(prefix="/format", tags=["Format"])

# Initialiser le service OpenAI
openai_service = OpenAIService()


class DocumentRequest(BaseModel):
    content: str
    enhance: Optional[bool] = True
    clean: Optional[bool] = True


class DocumentResponse(BaseModel):
    formatted_content: str
    summary: str
    word_count: int
    sections: list[str]


def format_vitepress_markdown(content: str) -> str:
    """Formate et améliore le contenu markdown VitePress en préservant ses fonctionnalités"""
    lines = content.split("\n")
    formatted_lines = []
    in_frontmatter = False
    frontmatter_lines = []

    for line in lines:
        # Préserver et améliorer le frontmatter YAML
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                frontmatter_lines.append(line)
                continue
            else:
                in_frontmatter = False
                # Ajouter des métadonnées manquantes si nécessaire
                frontmatter_content = "\n".join(frontmatter_lines[1:])
                if "lastUpdated:" not in frontmatter_content:
                    frontmatter_lines.append("lastUpdated: true")
                if "editLink:" not in frontmatter_content:
                    frontmatter_lines.append("editLink: true")
                frontmatter_lines.append(line)
                formatted_lines.extend(frontmatter_lines)
                frontmatter_lines = []
                continue

        if in_frontmatter:
            frontmatter_lines.append(line)
            continue

        # Préserver et améliorer les containers VitePress
        if line.strip().startswith("::: "):
            container_type = line.strip().split(" ")[1]
            # Ajouter des titres personnalisés si manquants
            if container_type in ["tip", "warning", "danger", "info", "details"]:
                if len(line.strip().split(" ")) == 2:  # Pas de titre personnalisé
                    titles = {
                        "tip": "Conseil",
                        "warning": "Attention",
                        "danger": "Important",
                        "info": "Information",
                        "details": "Détails",
                    }
                    line = f"::: {container_type} {titles.get(container_type, container_type.capitalize())}"

        # Améliorer les liens internes VitePress
        if "[" in line and "](" in line and not line.strip().startswith("!["):
            # Vérifier si c'est un lien interne sans extension
            link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
            matches = re.findall(link_pattern, line)
            for text, url in matches:
                if (
                    not url.startswith("http")
                    and not url.startswith("#")
                    and not url.endswith(".md")
                ):
                    if not url.endswith("/"):
                        line = line.replace(f"]({url})", f"]({url}.md)")

        formatted_lines.append(line)

    return "\n".join(formatted_lines)


def add_vitepress_utilities(content: str) -> str:
    """Ajoute des utilitaires VitePress pour améliorer la navigation et la présentation"""
    lines = content.split("\n")
    enhanced_lines = []
    has_frontmatter = False

    # Vérifier si le frontmatter existe
    if lines and lines[0].strip() == "---":
        has_frontmatter = True

    # Ajouter un frontmatter minimal si absent
    if not has_frontmatter:
        enhanced_lines.extend(
            ["---", "outline: deep", "lastUpdated: true", "editLink: true", "---", ""]
        )

    enhanced_lines.extend(lines)

    # Ajouter une table des matières si elle n'existe pas
    content_str = "\n".join(enhanced_lines)
    if "[[toc]]" not in content_str.lower():
        # Trouver la première section pour insérer la TOC
        for i, line in enumerate(enhanced_lines):
            if line.startswith("# ") and i > 0:
                enhanced_lines.insert(i + 1, "")
                enhanced_lines.insert(i + 2, "[[toc]]")
                enhanced_lines.insert(i + 3, "")
                break

    return "\n".join(enhanced_lines)


def extract_vitepress_metadata(content: str) -> dict:
    """Extrait les métadonnées VitePress du frontmatter"""
    metadata = {}
    lines = content.split("\n")
    in_frontmatter = False

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break

        if in_frontmatter and ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata


async def enhance_content_with_ai(content: str) -> str:
    """Améliore le contenu avec le service AI configuré (gpt-oss)"""
    try:
        # Vérifier que le service OpenAI est disponible
        health = await openai_service.health_check()
        if health["status"] != "healthy":
            print(
                f"Attention: Service AI non disponible ({health.get('error', 'Unknown error')}), amélioration ignorée"
            )
            return content

        messages = [
            {
                "role": "system",
                "content": """Tu es un expert en rédaction technique et documentation. 
                Tu améliores la documentation en français en corrigeant les erreurs grammaticales et orthographiques,
                en améliorant la clarté et la structure, et en ajoutant des exemples pertinents si nécessaire.
                Tu dois absolument préserver le format markdown et les spécificités VitePress.""",
            },
            {
                "role": "user",
                "content": f"""Améliore cette documentation en français tout en préservant le format markdown VitePress :

{content}

Instructions :
1. Corrige les erreurs grammaticales et orthographiques
2. Améliore la clarté et la structure
3. Ajoute des exemples pertinents si nécessaire
4. Garde strictement le format markdown et les containers VitePress
5. Préserve le frontmatter YAML
6. Améliore les titres pour qu'ils soient plus descriptifs

Contenu amélioré :""",
            },
        ]

        response = await openai_service.chat_completion(
            messages=messages, temperature=0.3, max_tokens=4000
        )

        enhanced_content = response["choices"][0]["message"]["content"].strip()
        return enhanced_content

    except Exception as e:
        # En cas d'erreur AI, retourner le contenu original
        print(f"Erreur lors de l'amélioration AI: {e}")
        return content


def extract_sections(content: str) -> list[str]:
    """Extrait les sections principales du markdown"""
    sections = []
    for line in content.split("\n"):
        if line.startswith("#"):
            # Supprimer les # et nettoyer
            section = line.lstrip("#").strip()
            if section:
                sections.append(section)
    return sections


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
        model_name = config.model_config or "AI"
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
        model_name = config.model_config or "AI"
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


async def format_vitepress_markdown_streaming(
    content: str,
) -> AsyncGenerator[str, None]:
    """Formate le contenu VitePress en streaming avec des chunks de progression"""
    yield (
        json.dumps({"status": "starting", "message": "Début du formatage VitePress..."})
        + "\n"
    )

    lines = content.split("\n")
    formatted_lines = []
    in_frontmatter = False
    frontmatter_lines = []
    total_lines = len(lines)

    for i, line in enumerate(lines):
        # Envoyer un chunk de progression tous les 50 lignes
        if i % 50 == 0:
            progress = (i / total_lines) * 30  # 30% pour le formatage VitePress
            yield (
                json.dumps(
                    {
                        "status": "formatting",
                        "progress": progress,
                        "message": f"Formatage VitePress: {i}/{total_lines} lignes...",
                    }
                )
                + "\n"
            )
            await asyncio.sleep(0.01)  # Petite pause pour le streaming

        # Préserver et améliorer le frontmatter YAML
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                frontmatter_lines.append(line)
                continue
            else:
                in_frontmatter = False
                # Ajouter des métadonnées manquantes si nécessaire
                frontmatter_content = "\n".join(frontmatter_lines[1:])
                if "lastUpdated:" not in frontmatter_content:
                    frontmatter_lines.append("lastUpdated: true")
                if "editLink:" not in frontmatter_content:
                    frontmatter_lines.append("editLink: true")
                frontmatter_lines.append(line)
                formatted_lines.extend(frontmatter_lines)
                frontmatter_lines = []
                continue

        if in_frontmatter:
            frontmatter_lines.append(line)
            continue

        # Préserver et améliorer les containers VitePress
        if line.strip().startswith("::: "):
            container_type = line.strip().split(" ")[1]
            if container_type in ["tip", "warning", "danger", "info", "details"]:
                if len(line.strip().split(" ")) == 2:
                    titles = {
                        "tip": "Conseil",
                        "warning": "Attention",
                        "danger": "Important",
                        "info": "Information",
                        "details": "Détails",
                    }
                    line = f"::: {container_type} {titles.get(container_type, container_type.capitalize())}"

        # Améliorer les liens internes VitePress
        if "[" in line and "](" in line and not line.strip().startswith("!["):
            link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
            matches = re.findall(link_pattern, line)
            for text, url in matches:
                if (
                    not url.startswith("http")
                    and not url.startswith("#")
                    and not url.endswith(".md")
                ):
                    if not url.endswith("/"):
                        line = line.replace(f"]({url})", f"]({url}.md)")

        formatted_lines.append(line)

    formatted_content = "\n".join(formatted_lines)
    yield (
        json.dumps(
            {
                "status": "vitepress_done",
                "progress": 30,
                "message": "Formatage VitePress terminé",
                "content_preview": formatted_content[:200] + "..."
                if len(formatted_content) > 200
                else formatted_content,
            }
        )
        + "\n"
    )


async def add_vitepress_utilities_streaming(content: str) -> AsyncGenerator[str, None]:
    """Ajoute les utilitaires VitePress en streaming"""
    yield (
        json.dumps(
            {
                "status": "adding_utilities",
                "progress": 40,
                "message": "Ajout des utilitaires VitePress...",
            }
        )
        + "\n"
    )
    await asyncio.sleep(0.1)

    lines = content.split("\n")
    enhanced_lines = []
    has_frontmatter = False

    if lines and lines[0].strip() == "---":
        has_frontmatter = True

    if not has_frontmatter:
        enhanced_lines.extend(
            ["---", "outline: deep", "lastUpdated: true", "editLink: true", "---", ""]
        )
        yield (
            json.dumps({"status": "utilities", "message": "Frontmatter ajouté"}) + "\n"
        )

    enhanced_lines.extend(lines)

    content_str = "\n".join(enhanced_lines)
    if "[[toc]]" not in content_str.lower():
        for i, line in enumerate(enhanced_lines):
            if line.startswith("# ") and i > 0:
                enhanced_lines.insert(i + 1, "")
                enhanced_lines.insert(i + 2, "[[toc]]")
                enhanced_lines.insert(i + 3, "")
                yield (
                    json.dumps(
                        {"status": "utilities", "message": "Table des matières ajoutée"}
                    )
                    + "\n"
                )
                break

    yield (
        json.dumps(
            {
                "status": "utilities_done",
                "progress": 50,
                "message": "Utilitaires VitePress ajoutés",
            }
        )
        + "\n"
    )


async def enhance_content_with_ai_streaming(content: str) -> AsyncGenerator[str, None]:
    """Améliore le contenu avec AI en streaming"""
    try:
        # Vérifier que le service AI est disponible
        health = await openai_service.health_check()
        if health["status"] != "healthy":
            yield (
                json.dumps(
                    {
                        "status": "ai_skipped",
                        "progress": 90,
                        "message": f"Service AI non disponible ({health.get('error', 'Unknown error')}), amélioration ignorée",
                    }
                )
                + "\n"
            )
            return

        model_name = config.model_config or "AI"
        yield (
            json.dumps(
                {
                    "status": "ai_starting",
                    "progress": 60,
                    "message": f"Amélioration avec {model_name} en cours...",
                }
            )
            + "\n"
        )

        # Diviser le contenu en chunks pour le traitement
        splitter = MarkdownTextSplitter(chunk_size=3000, chunk_overlap=200)
        chunks = splitter.split_text(content)

        enhanced_chunks = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            progress = 60 + (i / total_chunks) * 25  # 60% à 85%
            yield (
                json.dumps(
                    {
                        "status": "ai_processing",
                        "progress": progress,
                        "message": f"Traitement {model_name}: chunk {i + 1}/{total_chunks}",
                    }
                )
                + "\n"
            )

            enhanced_chunk = await enhance_content_with_ai(chunk)
            enhanced_chunks.append(enhanced_chunk)

            await asyncio.sleep(0.2)

        enhanced_content = "\n\n".join(enhanced_chunks)
        yield (
            json.dumps(
                {
                    "status": "ai_done",
                    "progress": 85,
                    "message": f"Amélioration {model_name} terminée",
                    "enhanced_content": enhanced_content,
                }
            )
            + "\n"
        )

    except Exception as e:
        yield (
            json.dumps(
                {
                    "status": "ai_error",
                    "progress": 85,
                    "message": f"Erreur AI: {str(e)}, contenu original conservé",
                    "enhanced_content": content,
                }
            )
            + "\n"
        )


async def process_document_streaming(
    content: str, clean: bool = True, enhance: bool = True
) -> AsyncGenerator[str, None]:
    """Traite un document complet en streaming avec AI"""
    model_name = config.model_config or "AI"
    yield (
        json.dumps(
            {
                "status": "start",
                "progress": 0,
                "message": f"Début du traitement du document avec {model_name}...",
            }
        )
        + "\n"
    )

    current_content = content

    # Étape 1: Formatage VitePress
    if clean:
        async for chunk in format_vitepress_markdown_streaming(current_content):
            yield chunk
        current_content = format_vitepress_markdown(current_content)

        async for chunk in add_vitepress_utilities_streaming(current_content):
            yield chunk
        current_content = add_vitepress_utilities(current_content)

    # Étape 2: Amélioration AI
    enhanced_content = current_content
    if enhance:
        enhanced_content_from_ai = None
        async for chunk in enhance_content_with_ai_streaming(current_content):
            chunk_data = json.loads(chunk.strip())
            if "enhanced_content" in chunk_data:
                enhanced_content_from_ai = chunk_data["enhanced_content"]
            yield chunk

        if enhanced_content_from_ai:
            enhanced_content = enhanced_content_from_ai
        else:
            enhanced_content = await enhance_content_with_ai(current_content)

    # Étape 3: Finalisation
    yield (
        json.dumps(
            {
                "status": "finalizing",
                "progress": 90,
                "message": "Finalisation du document...",
            }
        )
        + "\n"
    )

    sections = extract_sections(enhanced_content)
    word_count = len(enhanced_content.split())

    yield (
        json.dumps(
            {
                "status": "analyzing",
                "progress": 95,
                "message": f"Analyse terminée: {len(sections)} sections, {word_count} mots",
            }
        )
        + "\n"
    )

    # Résultat final
    final_result = {
        "status": "completed",
        "progress": 100,
        "message": "Traitement terminé avec succès",
        "result": {
            "formatted_content": enhanced_content,
            "summary": f"Document formaté avec {model_name}: {len(sections)} sections et {word_count} mots",
            "word_count": word_count,
            "sections": sections,
        },
    }

    yield json.dumps(final_result) + "\n"


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
