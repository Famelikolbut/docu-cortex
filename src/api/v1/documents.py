from fastapi import APIRouter, Depends, File, UploadFile, status

from src.models.documents import SummaryResponse, UploadResponse
from src.services.analysis_service import DocumentAnalysisService, analysis_service
from src.services.document_service import DocumentService, document_service

def get_document_service() -> DocumentService:
    return document_service

def get_analysis_service() -> DocumentAnalysisService:
    return analysis_service

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

@router.get(
    "/documents/{document_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_summary(
    document_id: str,
    service: DocumentAnalysisService = Depends(get_analysis_service),
) -> SummaryResponse:
    """
    Получает краткое содержание (summary) для указанного документа.
    """
    summary_text = await service.summarize_document(document_id)
    return SummaryResponse(document_id=document_id, summary=summary_text)