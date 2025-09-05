from fastapi import APIRouter, Depends, status
from src.models.chat import ChatRequest, ChatResponse
from src.services.chat_service import ChatService
from src.core.config import settings
from src.services.document_service import document_service

router = APIRouter(tags=["Chat"])


def get_chat_service() -> ChatService:
    return ChatService(settings=settings, document_service=document_service)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_with_document(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),  # <-- Магия FastAPI
):
    """
    Принимает ID документа и вопрос и возвращает структурированный ответ.
    """
    return await chat_service.query_document(
        document_id=request.document_id, question=request.question
    )
