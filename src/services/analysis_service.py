from __future__ import annotations
from typing import Optional
from pathlib import Path

from fastapi import HTTPException, status
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
from loguru import logger

from src.core.config import Settings
from src.services.document_service import DocumentService


class DocumentAnalysisService:
    def __init__(
            self,
            app_settings: Settings,
            document_service: DocumentService,
            llm: Optional[ChatOpenAI] = None,
    ):
        self.settings = app_settings
        self.document_service = document_service
        self.llm = llm or ChatOpenAI(
            model_name="gpt-4o",
            temperature=0,
            openai_api_key=self.settings.OPENAI_API_KEY.get_secret_value(),
        )
        self.prompt_template = self._load_prompt_template()

    @staticmethod
    def _load_prompt_template() -> PromptTemplate:
        template_path = (
                Path(__file__).parent.parent / "prompts" / "summary_prompt.jinja2"
        )
        template_str = template_path.read_text(encoding="utf-8")
        return PromptTemplate.from_template(template_str)

    async def summarize_document(self, document_id: str) -> str:
        logger.info(f"Запрос на краткое содержание для документа '{document_id}'")

        document_text = await self.document_service.get_document_content(document_id)
        if document_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден."
            )

        summarization_chain = self.prompt_template | self.llm | StrOutputParser()
        summary = await summarization_chain.ainvoke({"document_text": document_text})

        logger.success(f"Краткое содержание для '{document_id}' успешно создано.")
        return summary


from src.core.config import settings
from src.services.document_service import document_service as doc_service_instance

analysis_service = DocumentAnalysisService(
    app_settings=settings, document_service=doc_service_instance
)
