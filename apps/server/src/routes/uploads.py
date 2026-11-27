from dataclasses import dataclass

from fastapi import File, HTTPException, UploadFile, status

from src.core.config import settings

READ_BLOCK_BYTES = 64 * 1024


@dataclass
class TextUpload:
    filename: str
    content: str


async def _read_utf8(file: UploadFile) -> TextUpload:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Le fichier doit avoir un nom")
    raw = await _read_capped(file, settings.max_upload_bytes)
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="Le fichier doit être encodé en UTF-8"
        ) from None
    if len(content) > settings.max_content_chars:
        raise _too_large()
    return TextUpload(filename=file.filename, content=content)


async def _read_capped(file: UploadFile, limit: int) -> bytes:
    """Read the upload block by block, refusing it as soon as it passes `limit`."""
    if file.size is not None and file.size > limit:
        raise _too_large()
    blocks, total = [], 0
    while block := await file.read(READ_BLOCK_BYTES):
        total += len(block)
        if total > limit:
            raise _too_large()
        blocks.append(block)
    return b"".join(blocks)


def _too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large"
    )


async def read_text_upload(file: UploadFile = File(...)) -> TextUpload:
    """Read an uploaded text file: 400 when it is not UTF-8, 413 past the size limits."""
    return await _read_utf8(file)


async def read_markdown_upload(file: UploadFile = File(...)) -> TextUpload:
    """Read an uploaded Markdown file: 400 unless UTF-8 `.md`, 413 past the size limits."""
    if not (file.filename or "").endswith(".md"):
        raise HTTPException(
            status_code=400, detail="Le fichier doit être un fichier markdown (.md)"
        )
    return await _read_utf8(file)
