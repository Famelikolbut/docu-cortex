import uuid
from typing import Dict, Any
import fitz
from fastapi import UploadFile, HTTPException, status
from starlette.concurrency import run_in_threadpool
from src.core.logging import logger

db: Dict[str, Dict[str, Any]] = {}


class DocumentService:
    @staticmethod
    def _extract_text(file_contents: bytes, content_type: str) -> str:
        """Синхронная функция для извлечения текста, запускается в отдельном потоке."""
        if content_type == "application/pdf":
            with fitz.open(stream=file_contents, filetype="pdf") as doc:
                return "".join(page.get_text() for page in doc)
        elif content_type == "text/plain":
            return file_contents.decode("utf-8")
        else:
            raise ValueError(f"Неподдерживаемый тип файла: {content_type}")

    @staticmethod
    async def process_and_store_document(file: UploadFile) -> Dict[str, str]:
        logger.info(f"Starting processing of file: {file.filename}")
        try:
            file_contents = await file.read()
            text_content = await run_in_threadpool(
                DocumentService._extract_text, file_contents, file.content_type
            )
            if not text_content.strip():
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Не удалось извлечь текст из файла. Возможно, он пуст.",
                )
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Внутренняя ошибка при обработке файла.",
            )

        document_id = f"doc_{uuid.uuid4().hex}"
        db[document_id] = {"filename": file.filename, "content": text_content}
        logger.info(f"Successfully stored file: {file.filename} with id: {document_id}")
        return {"document_id": document_id, "filename": file.filename}


document_service = DocumentService()
