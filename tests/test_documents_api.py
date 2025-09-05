import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.api.v1.documents import get_document_service
from src.models.documents import UploadResponse


@pytest.fixture
def mocked_document_service_api(mock_document_service: MagicMock):
    """
    Фикстура для безопасной подмены DocumentService в API.
    """
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_document_success(
    client: AsyncClient,
    mock_document_service: MagicMock,
    mocked_document_service_api: None,  # Фикстура активируется просто по упоминанию
):
    """
    Тест успешной загрузки документа.
    """
    mock_response = UploadResponse(
        document_id="doc_test_123",
        filename="test.pdf",
        content_type="application/pdf",
    )
    mock_document_service.process_document = AsyncMock(return_value=mock_response)
    files = {"file": ("test.pdf", b"some pdf content", "application/pdf")}

    response = await client.post("/api/v1/documents", files=files)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["documentId"] == "doc_test_123"
    assert response_data["filename"] == "test.pdf"
    mock_document_service.process_document.assert_called_once()


@pytest.mark.asyncio
async def test_upload_document_unsupported_type(client: AsyncClient):
    """
    Тест загрузки файла неподдерживаемого типа.
    """
    files = {"file": ("test.zip", b"some zip content", "application/zip")}

    response = await client.post("/api/v1/documents", files=files)

    assert response.status_code == 400
    assert "Неподдерживаемый тип файла" in response.json()["detail"]
