import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.document_service import db


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    db.clear()


def test_upload_txt_file_success(client: TestClient):
    """
    Тест успешной загрузки TXT файла.
    """
    test_content = "Это тестовое содержимое для проверки загрузки."
    file_content_bytes = test_content.encode("utf-8")
    files = {"file": ("test.txt", file_content_bytes, "text/plain")}

    response = client.post("/api/v1/documents", files=files)

    assert response.status_code == 201
    response_data = response.json()
    assert "document_id" in response_data
    assert response_data["filename"] == "test.txt"

    document_id = response_data["document_id"]
    assert document_id in db
    stored_document = db[document_id]
    assert stored_document["filename"] == "test.txt"
    assert stored_document["content"] == test_content


def test_upload_unsupported_file_type_fails(client: TestClient):
    """
    Тест на загрузку файла неподдерживаемого типа.
    Ожидаем ошибку 400.
    """
    file_content_bytes = b"<xml>test</xml>"
    files = {"file": ("test.xml", file_content_bytes, "application/xml")}

    response = client.post("/api/v1/documents", files=files)

    assert response.status_code == 400
    assert "Неподдерживаемый тип файла" in response.json()["detail"]
