from fastapi import APIRouter, UploadFile, File, status
from src.models.documents import DocumentMetadata
from src.services.document_service import document_service

router = APIRouter()


@router.post(
    "/documents",
    response_model=DocumentMetadata,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Загрузка документа для анализа",
)
async def upload_document(
    file: UploadFile = File(..., description="Файл для загрузки (PDF или TXT)"),
):
    return await document_service.process_and_store_document(file)
