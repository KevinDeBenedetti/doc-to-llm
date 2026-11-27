from typing import Annotated, Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    app_name: str = "doc-to-llm"
    env: Literal["dev", "prod"] = "dev"
    # Keys accepted in X-API-Key, comma-separated in API_KEYS. With none, every
    # protected route answers 401. Declared after `env`, which its check reads.
    api_keys: Annotated[list[SecretStr], NoDecode] = Field(
        default=[], validate_default=True
    )
    # Browser origins allowed to call the API, comma-separated in CORS_ORIGINS.
    # Empty turns CORS off; "*" is refused.
    cors_origins: Annotated[list[str], NoDecode] = []
    openai_api_key: str
    openai_base_url: str | None = None
    openai_model: str | None = None
    log_file: str | None = None
    # Largest upload read, in bytes, and largest document accepted, in characters.
    max_upload_bytes: int = 10 * 1024 * 1024
    max_content_chars: int = 200_000

    @field_validator("api_keys", "cors_origins", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def refuse_wildcard_origin(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("CORS_ORIGINS must list origins, not '*'")
        return value

    # A field check, not a model one: its error then shows only this field's
    # value, never the whole input with OPENAI_API_KEY.
    @field_validator("api_keys")
    @classmethod
    def require_api_keys_in_prod(
        cls, value: list[SecretStr], info: ValidationInfo
    ) -> list[SecretStr]:
        if info.data.get("env") == "prod" and not value:
            raise ValueError("API_KEYS must be set when ENV=prod")
        return value


settings = Settings()
