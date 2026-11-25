from dataclasses import dataclass

from fastapi import File, HTTPException, UploadFile


@dataclass
class TextUpload:
    filename: str
    content: str


async def _read_utf8(file: UploadFile) -> TextUpload:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Le fichier doit avoir un nom")
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="Le fichier doit être encodé en UTF-8"
        ) from None
    return TextUpload(filename=file.filename, content=content)


async def read_text_upload(file: UploadFile = File(...)) -> TextUpload:
    """Read an uploaded text file, rejecting it with a 400 when it is not UTF-8."""
    return await _read_utf8(file)


async def read_markdown_upload(file: UploadFile = File(...)) -> TextUpload:
    """Read an uploaded Markdown file, rejecting anything but UTF-8 `.md` with a 400."""
    if not (file.filename or "").endswith(".md"):
        raise HTTPException(
            status_code=400, detail="Le fichier doit être un fichier markdown (.md)"
        )
    return await _read_utf8(file)
