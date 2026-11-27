from pydantic import BaseModel, Field

from src.schemas.content import BoundedContent


class TranslateRequest(BaseModel):
    content: BoundedContent = Field(..., description="Markdown content to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    model_name: str | None = Field(
        default=None, description="Model to use; defaults to OPENAI_MODEL"
    )


class TranslateResponse(BaseModel):
    translated_content: str
    source_language: str
    target_language: str
    model_used: str
    warnings: list[str] = []
