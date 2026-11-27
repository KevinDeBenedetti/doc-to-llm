from pydantic import BaseModel

from src.schemas.content import BoundedContent


class DocumentRequest(BaseModel):
    content: BoundedContent
    enhance: bool = True
    clean: bool = True


class DocumentResponse(BaseModel):
    formatted_content: str
    summary: str
    word_count: int
    sections: list[str]
    warnings: list[str] = []
