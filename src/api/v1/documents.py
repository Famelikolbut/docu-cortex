from fastapi import APIRouter, File, UploadFile, status, Depends

from src.models.documents import UploadResponse
from src.services.document_service import DocumentService, document_service


def get_document_service() -> DocumentService:
    return document_service


router = APIRouter(tags=["Documents"])


@router.post(
    "/documents",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> UploadResponse:
    """
    Загружает документ, извлекает из него текст и сохраняет для последующего анализа.
    Поддерживаемые форматы: PDF, TXT.
    """
    return await service.process_document(file)
