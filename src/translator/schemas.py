from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    content: str = Field(..., description="Markdown content to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    model_name: str = Field(default="gpt-oss", description="Model to use")


class TranslationResponse(BaseModel):
    translated_content: str
    source_language: str
    target_language: str
    model_used: str
