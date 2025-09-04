from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.logging import logger

@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

@app.get("/health", tags=["Health Check"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok"}