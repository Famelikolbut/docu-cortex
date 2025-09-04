from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Модель ответа с метаданными загруженного документа."""

    document_id: str = Field(
        ..., description="Уникальный идентификатор документа", examples=["doc_a1b2c3d4"]
    )
    filename: str = Field(
        ..., description="Имя загруженного файла", examples=["my_report.pdf"]
    )
