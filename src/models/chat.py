from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """Модель запроса для чата."""

    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(
        ...,
        alias="documentId",
        description="ID документа, к которому задается вопрос",
    )
    question: str = Field(..., description="Вопрос пользователя к документу")


class Source(BaseModel):
    """Модель для одного фрагмента-источника, использованного для ответа."""

    content: str = Field(..., description="Текст фрагмента-источника.")


class ChatResponse(BaseModel):
    """Структурированный ответ AI-ассистента."""

    model_config = ConfigDict(populate_by_name=True)

    answer: str = Field(
        ..., description="Синтезированный ответ на вопрос пользователя."
    )
    sources: List[Source] = Field(
        ...,
        description="Список фрагментов-источников, на основе которых был сгенерирован ответ.",
    )
    document_id: str = Field(
        ...,
        alias="documentId",
        description="ID документа, к которому был задан вопрос.",
    )
