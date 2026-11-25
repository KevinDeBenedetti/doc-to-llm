from pydantic import BaseModel


class DocumentRequest(BaseModel):
    content: str
    enhance: bool = True
    clean: bool = True


class DocumentResponse(BaseModel):
    formatted_content: str
    summary: str
    word_count: int
    sections: list[str]
    warnings: list[str] = []
