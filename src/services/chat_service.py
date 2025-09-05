from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

import chromadb
import openai
from fastapi import HTTPException, status
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from loguru import logger

from src.core.config import Settings
from src.models.chat import ChatResponse, Source
from src.services.document_service import DocumentService


class ChatService:
    def __init__(
        self,
        settings: Settings,
        document_service: DocumentService,
        llm: Optional[ChatOpenAI] = None,
        embeddings: Optional[OpenAIEmbeddings] = None,
        chroma_client: Optional[chromadb.Client] = None,
    ):
        self.settings = settings
        self.document_service = document_service
        self.llm = llm or ChatOpenAI(
            model_name="gpt-4o",
            temperature=0,
            openai_api_key=self.settings.OPENAI_API_KEY.get_secret_value(),
            max_retries=3,
        )
        self.embeddings = embeddings or OpenAIEmbeddings(
            openai_api_key=self.settings.OPENAI_API_KEY.get_secret_value()
        )
        self.chroma_client = chroma_client or chromadb.PersistentClient(
            path="chroma_data"
        )
        self.prompt_template = self._load_prompt_template()

    @staticmethod
    def _load_prompt_template() -> PromptTemplate:
        template_path = Path(__file__).parent.parent / "prompts" / "rag_prompt.jinja2"
        template_str = template_path.read_text(encoding="utf-8")
        return PromptTemplate.from_template(template_str)

    async def query_document(self, document_id: str, question: str) -> ChatResponse:
        logger.info(f"Запрос к документу '{document_id}' с вопросом: '{question}'")

        if await self._is_content_harmful(question):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый запрос."
            )

        vector_store = await self._get_or_create_vector_store(document_id)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        source_documents = await retriever.ainvoke(question)
        context = self._format_docs_from_metadata(source_documents)

        if not source_documents:
            answer = "Я не могу найти ответ на этот вопрос в данном документе. Пожалуйста, попробуйте переформулировать ваш запрос."
        else:
            rag_chain = (
                {"context": lambda x: x["context"], "question": lambda x: x["question"]}
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            answer = await rag_chain.ainvoke({"context": context, "question": question})

        if await self._is_content_harmful(answer):
            answer = (
                "Сгенерированный ответ был отфильтрован как потенциально небезопасный."
            )

        sources = [
            Source(content=doc.metadata.get("parent_content", doc.page_content))
            for doc in source_documents
        ]
        response = ChatResponse(answer=answer, sources=sources, document_id=document_id)

        logger.info(f"Сгенерированный ответ: {response.answer}")
        return response

    async def _get_or_create_vector_store(self, document_id: str) -> Chroma:
        document_text = await self.document_service.get_document_content(document_id)
        if document_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден."
            )

        collection_name = f"doc_{document_id.replace('-', '_')}"

        existing_collections = await asyncio.to_thread(
            self.chroma_client.list_collections
        )
        if collection_name not in [c.name for c in existing_collections]:
            logger.warning(
                f"База для документа {document_id} не найдена. Запуск индексации..."
            )
            parent_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000, chunk_overlap=200
            )
            child_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400, chunk_overlap=100
            )

            parent_docs = parent_splitter.create_documents([document_text])
            child_docs_with_metadata = []
            for parent_doc in parent_docs:
                child_splits = child_splitter.split_text(parent_doc.page_content)
                for split in child_splits:
                    child_doc = Document(
                        page_content=split,
                        metadata={"parent_content": parent_doc.page_content},
                    )
                    child_docs_with_metadata.append(child_doc)

            await Chroma.afrom_documents(
                documents=child_docs_with_metadata,
                embedding=self.embeddings,
                collection_name=collection_name,
                client=self.chroma_client,
            )
            logger.success(f"Новая база для документа {document_id} успешно создана.")
        else:
            logger.info(
                f"Найдена и загружена существующая база для документа {document_id}"
            )

        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            client=self.chroma_client,
        )

    async def _is_content_harmful(self, text: str) -> bool:
        try:
            client = openai.AsyncOpenAI(
                api_key=self.settings.OPENAI_API_KEY.get_secret_value(), max_retries=3
            )
            response = await client.moderations.create(input=text)
            return response.results[0].flagged
        except Exception as e:
            logger.error(f"Ошибка при вызове Moderation API после всех попыток: {e}")
            return True

    @staticmethod
    def _format_docs_from_metadata(docs: List[Document]) -> str:
        unique_parent_contents = set(
            doc.metadata.get("parent_content", doc.page_content) for doc in docs
        )
        return "\n\n---\n\n".join(unique_parent_contents)
