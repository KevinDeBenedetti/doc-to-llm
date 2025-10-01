from typing import Optional
import asyncio

from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
)

from src.core.config import settings


class TranslateService:
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.6):
        self.model_name = model_name or settings.openai_model
        self.temperature = temperature

    async def translate_markdown(
        self,
        content: str,
        source_language: str,
        target_language: str,
        model_name: Optional[str] = None,
    ) -> str:
        model = model_name or self.model_name

        def build_and_run():
            llm = ChatOpenAI(
                temperature=self.temperature,
                model_name=model,
                openai_api_key=settings.openai_api_key,
            )

            chat_prompt = ChatPromptTemplate.from_messages(
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

            chain = chat_prompt | llm

            result = chain.invoke(
                {
                    "content": content,
                    "source_language": source_language,
                    "target_language": target_language,
                }
            )

            return result.content

        translated = await asyncio.to_thread(build_and_run)
        return translated
