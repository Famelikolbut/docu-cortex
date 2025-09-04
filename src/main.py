from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.logging import logger
from src.api.v1 import documents  # <--- ДОБАВИТЬ ЭТУ СТРОКУ


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.include_router(documents.router, prefix="/api/v1")


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok"}
