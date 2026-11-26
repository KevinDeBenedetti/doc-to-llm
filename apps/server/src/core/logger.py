import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
)

# An opt-in log file stays bounded: 10 MB per file, plus 3 rotated backups.
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024
LOG_FILE_BACKUPS = 3


def build_handlers(log_file: str | None = None) -> list[logging.Handler]:
    """Log to stdout, and also to a rotating file when `log_file` is set."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(
            RotatingFileHandler(
                log_file,
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUPS,
                encoding="utf-8",
            )
        )
    return handlers


def setup_logging(level: int = logging.INFO, log_file: str | None = None):
    logging.basicConfig(
        level=level, format=LOG_FORMAT, handlers=build_handlers(log_file)
    )
