import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status

from src.main import app
from src.api.v1.documents import get_document_service, get_analysis_service
from src.models.documents import UploadResponse


@pytest.fixture
def mock_analysis_service() -> MagicMock:
    mock = MagicMock()
    mock.summarize_document = AsyncMock()
    return mock


@pytest.fixture
def mocked_document_service_api(mock_document_service: MagicMock):
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mocked_analysis_service_api(mock_analysis_service: MagicMock):
    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service
    yield
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("mocked_document_service_api")
@pytest.mark.asyncio
async def test_upload_document_success(
    client: AsyncClient,
    mock_document_service: MagicMock,
):
    """Тест успешной загрузки документа."""
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
    """Тест загрузки файла неподдерживаемого типа."""
    files = {"file": ("test.zip", b"some zip content", "application/zip")}
    response = await client.post("/api/v1/documents", files=files)
    assert response.status_code == 400
    assert "Неподдерживаемый тип файла" in response.json()["detail"]


@pytest.mark.usefixtures("mocked_analysis_service_api")
@pytest.mark.asyncio
async def test_get_summary_success(
    client: AsyncClient,
    mock_analysis_service: MagicMock,
):
    """Тест успешного получения краткого содержания документа."""
    doc_id = "doc_test_123"
    expected_summary = "Это краткое содержание документа."
    mock_analysis_service.summarize_document.return_value = expected_summary

    response = await client.get(f"/api/v1/documents/{doc_id}/summary")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["document_id"] == doc_id
    assert response_data["summary"] == expected_summary
    mock_analysis_service.summarize_document.assert_called_once_with(doc_id)


@pytest.mark.usefixtures("mocked_analysis_service_api")
@pytest.mark.asyncio
async def test_get_summary_not_found(
    client: AsyncClient,
    mock_analysis_service: MagicMock,
):
    """Тест получения summary для несуществующего документа."""
    doc_id = "doc_not_found"
    mock_analysis_service.summarize_document.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден."
    )

    response = await client.get(f"/api/v1/documents/{doc_id}/summary")

    assert response.status_code == 404
    assert "Документ не найден" in response.json()["detail"]
