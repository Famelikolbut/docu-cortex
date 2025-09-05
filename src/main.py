from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.core.logging import logger
from src.api.v1 import chat, documents
from src.core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Приложение запущено")
    yield
    logger.info("Приложение остановлено")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health", tags=["Health Check"])
async def health_check() -> dict[str, str]:
    """
    Проверка состояния сервиса.
    """
    return {"status": "ok"}
