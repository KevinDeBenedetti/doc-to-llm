import logging
from dataclasses import dataclass, field
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.core.config import settings
from src.services.vitepress import split_into_chunks

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a professional translator specialized in technical documentation and Markdown.",
        ),
        (
            "human",
            "Translate the following Markdown content from {source_language} to {target_language}.\n"
            "Preserve all Markdown formatting, links and structure.\n\n"
            "Content:\n"
            "{content}\n",
        ),
    ]
)


@dataclass
class TranslateResult:
    content: str
    warnings: list[str] = field(default_factory=list)


def build_chat_model(model: str, temperature: float) -> ChatOpenAI:
    """Create the chat model that translates the chunks of a document.

    The endpoint comes from `settings`, as for formatting: left out, the client
    would look up `OPENAI_API_BASE`, then `OPENAI_BASE_URL`, on its own.
    """
    return ChatOpenAI(
        temperature=temperature,
        model_name=model,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
    )


class TranslateService:
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.6):
        self.model_name = model_name or settings.openai_model
        self.temperature = temperature

    async def translate_markdown(
        self,
        content: str,
        source_language: str,
        target_language: str,
    ) -> TranslateResult:
        """Translate the document chunk by chunk.

        A chunk whose reply the token limit cut keeps its source text, with a
        warning, so the result never silently misses the end of a chunk.
        """
        chain = PROMPT | build_chat_model(self.model_name, self.temperature)
        chunks = split_into_chunks(content)
        translated = []
        warnings = []
        for i, chunk in enumerate(chunks):
            reply = await chain.ainvoke(
                {
                    "content": chunk,
                    "source_language": source_language,
                    "target_language": target_language,
                }
            )
            if reply.response_metadata.get("finish_reason") == "length":
                label = f"chunk {i + 1}/{len(chunks)}"
                logger.warning("Translation truncated by the token limit for %s", label)
                warnings.append(
                    f"Translation truncated (token limit) on {label}, source text kept"
                )
                translated.append(chunk)
            else:
                translated.append(reply.content.strip())
        return TranslateResult(content="\n\n".join(translated), warnings=warnings)
