from typing import Optional
from dataclasses import dataclass, field
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    app_name: str = "doc-to-llm"

    ai_provider: Optional[str] = field(default_factory=lambda: os.getenv("AI_PROVIDER"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_API_BASE"))
    model_config: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-oss")
    )


config = Config()
