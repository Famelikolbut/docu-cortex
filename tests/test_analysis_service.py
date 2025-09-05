import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from src.services.analysis_service import DocumentAnalysisService
from src.core.config import Settings


@pytest.fixture
def analysis_service(
        mock_document_service: MagicMock,
        mock_llm: MagicMock
) -> DocumentAnalysisService:
    """Фикстура, создающая экземпляр DocumentAnalysisService с моками."""
    settings = Settings(OPENAI_API_KEY="test_key")
    return DocumentAnalysisService(
        app_settings=settings,
        document_service=mock_document_service,
        llm=mock_llm,
    )


@pytest.mark.asyncio
async def test_summarize_document_success(
        analysis_service: DocumentAnalysisService,
        mock_document_service: MagicMock,
        mock_llm: MagicMock,
):
    """Тест успешной суммаризации документа на уровне сервиса."""
    doc_id = "doc_exists"
    doc_content = "Это полный текст документа, который нужно сократить."
    expected_summary = "Краткое содержание."

    mock_document_service.get_document_content = AsyncMock(return_value=doc_content)
    mock_llm.ainvoke = AsyncMock(return_value=expected_summary)

    summary = await analysis_service.summarize_document(doc_id)

    assert summary == expected_summary
    mock_document_service.get_document_content.assert_called_once_with(doc_id)
    call_args = mock_llm.ainvoke.call_args[0][0]
    final_prompt_string = str(call_args)
    assert doc_content in final_prompt_string


@pytest.mark.asyncio
async def test_summarize_document_not_found(
        analysis_service: DocumentAnalysisService,
        mock_document_service: MagicMock,
):
    """Тест ошибки при запросе summary для несуществующего документа."""
    doc_id = "doc_not_found"
    mock_document_service.get_document_content = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await analysis_service.summarize_document(doc_id)

    assert exc_info.value.status_code == 404
    assert "Документ не найден" in exc_info.value.detail
