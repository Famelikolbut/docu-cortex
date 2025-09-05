import sys
from loguru import logger
from src.core.config import settings

logger.remove()

logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL.upper(),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    colorize=True,
)
