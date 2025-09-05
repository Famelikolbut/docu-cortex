from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.v1 import chat, documents
from src.core.config import settings
from src.core.logging import logger


# Менеджер Lifespan
@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Приложение запущено")
    yield
    logger.info("Приложение остановлено")


# Инициализация приложения
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    description="Сервис для чата с документами с использованием RAG.",
    version="0.1.0",
)

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API роутер
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


# Роутер для Frontend и служб
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", tags=["Health Check"])
async def health_check() -> dict[str, str]:
    """
    Проверка состояния сервиса.
    """
    return {"status": "ok"}
