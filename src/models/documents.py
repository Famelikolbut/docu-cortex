from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class UploadResponse(BaseModel):
    """Модель ответа с метаданными загруженного документа."""

    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(
        ...,
        alias="documentId",
        description="Уникальный идентификатор документа",
        examples=["doc_a1b2c3d4"],
    )
    filename: str = Field(
        ...,
        description="Имя загруженного файла",
        examples=["my_report.pdf"],
    )
    content_type: str = Field(
        ...,
        alias="contentType",
        description="MIME-тип загруженного файла",
        examples=["application/pdf"],
    )


class SummaryResponse(BaseModel):
    """Модель ответа с кратким содержанием документа."""

    document_id: str = Field(
        ...,
        description="Уникальный идентификатор документа",
        examples=["doc_a1b2c3d4"],
    )
    summary: str = Field(
        ...,
        description="Сгенерированное краткое содержание документа",
        examples=["В документе рассматриваются основные принципы..."],
    )
