import pytest
from unittest.mock import MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from src.core.config import Settings
from src.services.document_service import DocumentService
from langchain_openai import ChatOpenAI
from src.main import app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Возвращает объект Settings для тестирования.
    """
    return Settings(OPENAI_API_KEY="test_key")


@pytest.fixture
def mock_document_service() -> MagicMock:
    """
    Создает mock для DocumentService.
    """
    mock = MagicMock(spec=DocumentService)
    mock.get_document_content = AsyncMock(return_value="Какой-то текст документа.")
    return mock


@pytest.fixture
def mock_llm() -> MagicMock:
    """
    Mock для языковой модели ChatOpenAI.
    """
    mock = MagicMock(spec=ChatOpenAI)
    mock.ainvoke = AsyncMock(return_value="безопасный ответ от LLM")
    return mock


@pytest.fixture
async def client() -> AsyncClient:
    """
    Фикстура, предоставляющая асинхронный клиент для тестирования API.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
