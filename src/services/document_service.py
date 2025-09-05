from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
import fitz
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from src.models.documents import UploadResponse


class DocumentService:
    """
    Сервис для обработки и управления документами.
    """

    _storage_path = Path("documents_storage")

    def __init__(self):
        self._storage_path.mkdir(exist_ok=True)

    async def process_document(self, file: UploadFile) -> UploadResponse:
        """
        Обрабатывает загруженный файл, извлекает текст и сохраняет его.
        """
        logger.info(f"Обработка файла: {file.filename}")

        content_type = file.content_type
        if content_type == "application/pdf":
            text = await self._extract_text_from_pdf(file)
        elif content_type == "text/plain":
            text = await self._extract_text_from_txt(file)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый тип файла. Пожалуйста, используйте PDF или TXT.",
            )

        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Загруженный документ пуст.",
            )

        doc_id = f"doc_{uuid.uuid4().hex}"
        await self._save_text_to_file(doc_id, text)

        return UploadResponse(
            document_id=doc_id,
            filename=file.filename,
            content_type=content_type,
        )

    async def get_document_content(self, doc_id: str) -> Optional[str]:
        """
        Получает текстовое содержимое документа по его ID.
        """
        return await self._read_text_from_file(doc_id)

    async def _save_text_to_file(self, doc_id: str, text: str) -> None:
        file_path = self._storage_path / f"{doc_id}.txt"
        try:
            async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
                await f.write(text)
            logger.success(f"Текст для документа {doc_id} сохранен в {file_path}")
        except IOError as e:
            logger.error(f"Ошибка сохранения файла для {doc_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось сохранить обработанный документ.",
            )

    async def _read_text_from_file(self, doc_id: str) -> Optional[str]:
        file_path = self._storage_path / f"{doc_id}.txt"
        if not file_path.exists():
            return None
        try:
            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                return await f.read()
        except IOError as e:
            logger.error(f"Ошибка чтения файла для {doc_id}: {e}")
            return None

    async def _extract_text_from_pdf(self, file: UploadFile) -> str:
        content = await file.read()
        return await asyncio.to_thread(self._extract_text_from_pdf_sync, content)

    @staticmethod
    def _extract_text_from_pdf_sync(content: bytes) -> str:
        try:
            with fitz.open(stream=content, filetype="pdf") as doc:
                return "".join(page.get_text() for page in doc)
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось обработать PDF файл.",
            )

    @staticmethod
    async def _extract_text_from_txt(file: UploadFile) -> str:
        content = await file.read()
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.error(f"Ошибка декодирования TXT файла: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось декодировать TXT файл. Убедитесь, что он в кодировке UTF-8.",
            )


document_service = DocumentService()
