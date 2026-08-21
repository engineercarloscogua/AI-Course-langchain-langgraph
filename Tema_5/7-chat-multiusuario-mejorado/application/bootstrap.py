"""Punto de composición de dependencias de la aplicación.

Este es el único módulo que conoce simultáneamente las implementaciones
concretas. En tests se omite y se construye ChatApplicationService con dobles.
"""

from dataclasses import dataclass
import os

from langchain_openai import OpenAIEmbeddings

from agent.engine import LangChainAgentGateway
from application.chat_service import ChatApplicationService
from application.knowledge_service import KnowledgeApplicationService
from config import (
    CHECKPOINT_DB_PATH,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_FILES_DIR,
    MEMORY_DB_PATH,
    METADATA_DB_PATH,
    SETTINGS,
)
from infrastructure.knowledge_repository import SQLiteKnowledgeRepository
from infrastructure.metadata_repository import SQLiteMetadataRepository
from infrastructure.pdf_ingestion import LegalDocumentChunker, PDFTextExtractor


@dataclass(slots=True)
class ApplicationContainer:
    """Mantiene vivas las conexiones compartidas durante la sesión del servidor."""

    metadata: SQLiteMetadataRepository
    knowledge: SQLiteKnowledgeRepository
    agent: LangChainAgentGateway
    chat_service: ChatApplicationService
    knowledge_service: KnowledgeApplicationService


def build_application() -> ApplicationContainer:
    """Construye una vez todos los adaptadores y los conecta a sus casos de uso."""

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "No se encontró OPENAI_API_KEY. Agrégala al archivo .env de la raíz."
        )

    metadata = SQLiteMetadataRepository(METADATA_DB_PATH)
    knowledge_embeddings = OpenAIEmbeddings(
        model=SETTINGS.embedding_model,
        dimensions=SETTINGS.embedding_dimensions,
    )
    knowledge = SQLiteKnowledgeRepository(
        database_path=KNOWLEDGE_DB_PATH,
        embeddings=knowledge_embeddings,
        embedding_dimensions=SETTINGS.embedding_dimensions,
        max_results=SETTINGS.max_knowledge_results,
    )
    agent = LangChainAgentGateway(
        settings=SETTINGS,
        checkpoint_path=CHECKPOINT_DB_PATH,
        memory_path=MEMORY_DB_PATH,
        knowledge=knowledge,
    )
    service = ChatApplicationService(
        metadata=metadata,
        agent=agent,
        max_input_characters=SETTINGS.max_input_characters,
    )
    knowledge_service = KnowledgeApplicationService(
        repository=knowledge,
        extractor=PDFTextExtractor(),
        chunker=LegalDocumentChunker(SETTINGS.max_legal_chunk_characters),
        documents_directory=KNOWLEDGE_FILES_DIR,
        max_pdf_bytes=SETTINGS.max_pdf_bytes,
    )
    return ApplicationContainer(
        metadata=metadata,
        knowledge=knowledge,
        agent=agent,
        chat_service=service,
        knowledge_service=knowledge_service,
    )
