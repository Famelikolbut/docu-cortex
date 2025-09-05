import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from langchain_core.documents import Document

from src.services.chat_service import ChatService


@pytest.fixture
def mock_retriever() -> AsyncMock:
    """Мок для ретривера, который возвращает документы."""
    mock = AsyncMock()
    mock.ainvoke.return_value = [Document(page_content="релевантный контекст")]
    return mock


@pytest.fixture
def chat_service(
    test_settings,
    mock_document_service,
    mock_llm,
    mocker,
    mock_retriever,
) -> ChatService:
    """
    Фикстура, которая предоставляет экземпляр ChatService, полностью изолированный
    от внешних зависимостей и файловой системы.
    """
    mocker.patch(
        "src.services.chat_service.ChatService._get_or_create_vector_store",
        return_value=MagicMock(as_retriever=MagicMock(return_value=mock_retriever)),
    )

    service = ChatService(
        settings=test_settings,
        document_service=mock_document_service,
        llm=mock_llm,
    )
    return service


@pytest.mark.asyncio
async def test_query_document_harmful_question(chat_service: ChatService, mocker):
    """Тест, что вредоносный вопрос блокируется."""
    mock_harmful_check = mocker.patch.object(
        chat_service, "_is_content_harmful", new_callable=AsyncMock, return_value=True
    )
    with pytest.raises(HTTPException) as exc_info:
        await chat_service.query_document("doc_id", "a harmful question")

    assert exc_info.value.status_code == 400
    mock_harmful_check.assert_called_once_with("a harmful question")


@pytest.mark.asyncio
async def test_query_document_no_relevant_docs(
    chat_service: ChatService, mock_retriever, mocker
):
    """Тест случая, когда не найдено релевантных документов."""
    mocker.patch.object(
        chat_service, "_is_content_harmful", new_callable=AsyncMock, return_value=False
    )
    mock_retriever.ainvoke.return_value = []

    response = await chat_service.query_document("doc_id", "нерелевантный вопрос")

    assert "не могу найти ответ" in response.answer
    assert response.sources == []
    chat_service.llm.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_query_document_harmful_answer(
    chat_service: ChatService, mock_llm, mocker
):
    """Тест случая, когда сгенерирован вредоносный ответ."""
    mock_harmful_check = mocker.patch.object(
        chat_service, "_is_content_harmful", new_callable=AsyncMock
    )
    mock_harmful_check.side_effect = [False, True]
    mock_llm.ainvoke.return_value = "a harmful answer"

    response = await chat_service.query_document("doc_id", "безопасный вопрос")

    assert "отфильтрован как потенциально небезопасный" in response.answer
    assert mock_harmful_check.call_count == 2


@pytest.mark.asyncio
async def test_query_document_success(chat_service: ChatService, mock_llm, mocker):
    """Тест успешного сценария выполнения запроса к документу."""
    mocker.patch.object(
        chat_service, "_is_content_harmful", new_callable=AsyncMock, return_value=False
    )

    response = await chat_service.query_document("doc_id", "релевантный вопрос")

    assert response.answer == "безопасный ответ от LLM"
    assert len(response.sources) == 1
    assert response.sources[0].content == "релевантный контекст"
    mock_llm.ainvoke.assert_called_once()
