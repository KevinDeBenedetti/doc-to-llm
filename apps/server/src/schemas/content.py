from typing import Annotated

from pydantic import AfterValidator

from src.core.config import settings


def _check_length(content: str) -> str:
    # Read at validation time, so MAX_CONTENT_CHARS applies without a schema rebuild.
    if len(content) > settings.max_content_chars:
        raise ValueError(
            f"content is longer than {settings.max_content_chars} characters"
        )
    return content


# Document text sent to the LLM: at most MAX_CONTENT_CHARS characters.
BoundedContent = Annotated[str, AfterValidator(_check_length)]
