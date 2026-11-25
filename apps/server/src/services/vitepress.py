import logging
import re
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from langchain.text_splitter import MarkdownTextSplitter

from src.core.config import settings
from src.services.openai import OpenAIService

logger = logging.getLogger(__name__)

# Size of the pieces sent to the AI, in characters. No overlap: each piece is
# rewritten on its own and the results are joined, so shared text would repeat.
CHUNK_SIZE = 3000
MAX_TOKENS = 4000

SYSTEM_PROMPT = """Tu es un expert en rédaction technique et documentation.
Tu améliores la documentation en français en corrigeant les erreurs grammaticales et orthographiques,
en améliorant la clarté et la structure, et en ajoutant des exemples pertinents si nécessaire.
Tu dois absolument préserver le format markdown et les spécificités VitePress."""

USER_PROMPT = """Améliore cette documentation en français tout en préservant le format markdown VitePress :

{content}

Instructions :
1. Corrige les erreurs grammaticales et orthographiques
2. Améliore la clarté et la structure
3. Ajoute des exemples pertinents si nécessaire
4. Garde strictement le format markdown et les containers VitePress
5. Préserve le frontmatter YAML
6. Améliore les titres pour qu'ils soient plus descriptifs

Contenu amélioré :"""


@lru_cache
def get_openai_service() -> OpenAIService:
    """Create the AI client on first use, so importing this module needs no network setup."""
    return OpenAIService()


def extract_sections(content: str) -> list[str]:
    """Extract the Markdown headings, without their `#` markers."""
    sections = []
    for line in content.split("\n"):
        if line.startswith("#"):
            section = line.lstrip("#").strip()
            if section:
                sections.append(section)
    return sections


CONTAINER_TITLES = {
    "tip": "Conseil",
    "warning": "Attention",
    "danger": "Important",
    "info": "Information",
    "details": "Détails",
}

FRONTMATTER_DEFAULTS = {"lastUpdated": "true", "editLink": "true"}


def split_frontmatter(lines: list[str]) -> tuple[list[str] | None, list[str]]:
    """Split a leading YAML frontmatter block from the body.

    Only a `---` on the first line opens frontmatter, and the next `---` closes
    it. Returns (frontmatter lines between the delimiters, body lines), or
    (None, lines) when there is no complete frontmatter block.
    """
    if not lines or lines[0].strip() != "---":
        return None, lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :]
    return None, lines


def format_frontmatter(frontmatter: list[str]) -> list[str]:
    """Add the VitePress metadata the frontmatter is missing."""
    keys = {line.split(":", 1)[0].strip() for line in frontmatter if ":" in line}
    added = [
        f"{key}: {value}"
        for key, value in FRONTMATTER_DEFAULTS.items()
        if key not in keys
    ]
    return ["---", *frontmatter, *added, "---"]


def format_container(line: str) -> str:
    """Give a VitePress container without a custom title a default one."""
    parts = line.strip().split(" ")
    if parts[0] == ":::" and len(parts) == 2 and parts[1] in CONTAINER_TITLES:
        return f"::: {parts[1]} {CONTAINER_TITLES[parts[1]]}"
    return line


LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")


def to_internal_page_link(target: str) -> str:
    """Add `.md` to a link to another page; leave every other target as is."""
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not parts.path:
        return target
    last_segment = parts.path.rsplit("/", 1)[-1]
    if not last_segment or "." in last_segment:
        return target
    return urlunsplit(parts._replace(path=f"{parts.path}.md"))


def rewrite_internal_links(line: str) -> str:
    """Point internal page links at their `.md` file, skipping image embeds."""
    return LINK_PATTERN.sub(
        lambda m: f"[{m.group(1)}]({to_internal_page_link(m.group(2))})", line
    )


def format_line(line: str) -> str:
    """Apply the body formatting rules to one line."""
    if line.strip().startswith("::: "):
        line = format_container(line)
    return rewrite_internal_links(line)


def format_vitepress_markdown(content: str) -> str:
    """Format VitePress Markdown while preserving its features."""
    frontmatter, body = split_frontmatter(content.split("\n"))
    formatted = format_frontmatter(frontmatter) if frontmatter is not None else []
    in_code = False
    for line in body:
        # Fenced code is example content: leave it exactly as written.
        if line.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
            formatted.append(line)
        else:
            formatted.append(line if in_code else format_line(line))
    return "\n".join(formatted)


def add_vitepress_utilities(content: str) -> str:
    """Add a default frontmatter and a table of contents when they are missing."""
    lines = content.split("\n")
    enhanced_lines = []
    has_frontmatter = False

    if lines and lines[0].strip() == "---":
        has_frontmatter = True

    # Add a minimal frontmatter when there is none
    if not has_frontmatter:
        enhanced_lines.extend(
            ["---", "outline: deep", "lastUpdated: true", "editLink: true", "---", ""]
        )

    enhanced_lines.extend(lines)

    # Add a table of contents when there is none
    content_str = "\n".join(enhanced_lines)
    if "[[toc]]" not in content_str.lower():
        # Insert it after the first top-level heading
        for i, line in enumerate(enhanced_lines):
            if line.startswith("# ") and i > 0:
                enhanced_lines.insert(i + 1, "")
                enhanced_lines.insert(i + 2, "[[toc]]")
                enhanced_lines.insert(i + 3, "")
                break

    return "\n".join(enhanced_lines)


def extract_vitepress_metadata(content: str) -> dict:
    """Read the frontmatter keys and values into a dict."""
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


@dataclass
class FormatResult:
    formatted_content: str
    summary: str
    word_count: int
    sections: list[str]
    warnings: list[str] = field(default_factory=list)


def split_into_chunks(content: str) -> list[str]:
    """Split a document into the pieces sent to the AI, without overlap."""
    return MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=0).split_text(
        content
    )


async def enhance_chunk(service: OpenAIService, chunk: str) -> str | None:
    """Rewrite one piece with the AI; None when the reply hit the token limit."""
    response = await service.chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(content=chunk)},
        ],
        temperature=0.3,
        max_tokens=MAX_TOKENS,
    )
    choice = response["choices"][0]
    if choice.get("finish_reason") == "length":
        return None
    return choice["message"]["content"].strip()


def _event(status: str, progress: float, message: str, **extra: Any) -> dict:
    return {"status": status, "progress": progress, "message": message, **extra}


def _preview(content: str) -> str:
    return content[:200] + "..." if len(content) > 200 else content


async def iter_format_document(
    content: str, clean: bool = True, enhance: bool = True
) -> AsyncGenerator[dict, None]:
    """Run the format pipeline, yielding a progress event after each step.

    The last event has the status "completed" and carries the result. Every
    endpoint runs this one pipeline: the streaming ones forward the events, the
    others keep the result (see `format_document`).
    """
    model_name = settings.openai_model or "AI"
    warnings: list[str] = []
    yield _event("start", 0, f"Début du traitement du document avec {model_name}...")

    if clean:
        content = format_vitepress_markdown(content)
        yield _event(
            "vitepress_done",
            30,
            "Formatage VitePress terminé",
            content_preview=_preview(content),
        )
        content = add_vitepress_utilities(content)
        yield _event("utilities_done", 50, "Utilitaires VitePress ajoutés")

    if enhance:
        async for event in _iter_enhance(content, model_name, warnings):
            if "enhanced_content" in event:
                content = event["enhanced_content"]
            yield event

    yield _event("finalizing", 90, "Finalisation du document...")

    sections = extract_sections(content)
    word_count = len(content.split())
    result = FormatResult(
        formatted_content=content,
        summary=f"Document formaté avec {model_name}: {len(sections)} sections et {word_count} mots",
        word_count=word_count,
        sections=sections,
        warnings=warnings,
    )
    yield _event(
        "completed", 100, "Traitement terminé avec succès", result=asdict(result)
    )


async def _iter_enhance(
    content: str, model_name: str, warnings: list[str]
) -> AsyncGenerator[dict, None]:
    """Enhance the document piece by piece; a piece that fails is kept as is."""
    try:
        service = get_openai_service()
        health = await service.health_check()
    except Exception:
        logger.exception("AI service unavailable")
        health = {"status": "unhealthy", "error": "client error"}

    if health["status"] != "healthy":
        error = health.get("error", "Unknown error")
        message = f"Service AI non disponible ({error}), amélioration ignorée"
        logger.warning("AI service unhealthy, enhancement skipped: %s", error)
        warnings.append(message)
        yield _event("ai_skipped", 90, message)
        return

    yield _event("ai_starting", 60, f"Amélioration avec {model_name} en cours...")

    chunks = split_into_chunks(content)
    enhanced_chunks = []
    for i, chunk in enumerate(chunks):
        label = f"chunk {i + 1}/{len(chunks)}"
        yield _event(
            "ai_processing",
            60 + (i / len(chunks)) * 25,
            f"Traitement {model_name}: {label}",
        )
        try:
            enhanced = await enhance_chunk(service, chunk)
        except Exception:
            logger.exception("AI enhancement failed for %s", label)
            enhanced = None
            warnings.append(f"Erreur AI sur le {label}, contenu original conservé")
        else:
            if enhanced is None:
                logger.warning("AI reply truncated by the token limit for %s", label)
                warnings.append(
                    f"Réponse AI tronquée (limite de tokens) sur le {label}, contenu original conservé"
                )
        enhanced_chunks.append(enhanced if enhanced is not None else chunk)

    yield _event(
        "ai_done",
        85,
        f"Amélioration {model_name} terminée",
        enhanced_content="\n\n".join(enhanced_chunks),
    )


async def format_document(
    content: str, clean: bool = True, enhance: bool = True
) -> FormatResult:
    """Run the format pipeline and return its result."""
    async for event in iter_format_document(content, clean, enhance):
        if event["status"] == "completed":
            return FormatResult(**event["result"])
    raise RuntimeError("Format pipeline ended without a result")
