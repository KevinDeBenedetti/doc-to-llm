import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str | None = Security(api_key_header)) -> None:
    """Refuse the request with a 401 unless X-API-Key is one of API_KEYS."""
    # Compare as bytes, against every key, in constant time: timing reveals
    # nothing, and a non-ASCII header is refused instead of raising.
    given = (key or "").encode()
    matches = [
        hmac.compare_digest(given, allowed.get_secret_value().encode())
        for allowed in settings.api_keys
    ]
    if not key or not any(matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
