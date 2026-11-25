from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "doc-to-llm"
    openai_api_key: str
    openai_base_url: str | None = None
    openai_model: str | None = None


settings = Settings()
