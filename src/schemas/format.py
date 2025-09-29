from pydantic import BaseModel
from typing import Optional


class DocumentRequest(BaseModel):
    content: str
    enhance: Optional[bool] = True
    clean: Optional[bool] = True


class DocumentResponse(BaseModel):
    formatted_content: str
    summary: str
    word_count: int
    sections: list[str]
