"""Contratos que desacoplan los casos de uso de sus implementaciones.

Un ``Protocol`` cumple una función parecida a una interfaz en otros lenguajes:
define qué operaciones necesita la aplicación, pero no obliga a que sean
SQLite, OpenAI o LangGraph. Los tests pueden reemplazarlas por objetos falsos.
"""

from typing import Protocol

from domain.models import (
    AgentReply,
    Chat,
    ChatMessage,
    MemoryRecord,
    LegalSection,
    NormativeChunk,
    NormativeDocument,
    NormativeDocumentStatus,
    NormativeSearchResult,
    PDFPage,
    User,
)


class MetadataRepositoryPort(Protocol):
    """Operaciones necesarias para administrar usuarios y chats."""

    def ensure_default_user(self) -> User: ...

    def create_user(self, display_name: str) -> User: ...

    def list_users(self) -> list[User]: ...

    def get_user(self, user_id: str) -> User | None: ...

    def create_chat(self, user_id: str) -> Chat: ...

    def list_chats(self, user_id: str) -> list[Chat]: ...

    def get_chat(self, user_id: str, chat_id: str) -> Chat | None: ...

    def record_turn(self, user_id: str, chat_id: str, first_message: str) -> Chat: ...

    def delete_chat(self, user_id: str, chat_id: str) -> bool: ...


class AgentGatewayPort(Protocol):
    """Frontera entre los casos de uso y la implementación agentic."""

    def reply(self, user_id: str, chat_id: str, message: str) -> AgentReply: ...

    def history(self, user_id: str, chat_id: str) -> list[ChatMessage]: ...

    def delete_thread(self, user_id: str, chat_id: str) -> None: ...

    def list_memories(self, user_id: str) -> list[MemoryRecord]: ...

    def delete_memory(self, user_id: str, memory_key: str) -> None: ...


class NormativeKnowledgeSearchPort(Protocol):
    """Consulta de solo lectura usada por el agente y sus herramientas."""

    def search(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[NormativeSearchResult]: ...


class NormativeKnowledgeRepositoryPort(NormativeKnowledgeSearchPort, Protocol):
    """Contrato completo usado por los casos de uso administrativos."""

    def add_document(
        self,
        document: NormativeDocument,
        chunks: list[NormativeChunk],
    ) -> None: ...

    def get_document(self, document_id: str) -> NormativeDocument | None: ...

    def find_by_checksum(
        self,
        checksum_sha256: str,
    ) -> NormativeDocument | None: ...

    def list_documents(self) -> list[NormativeDocument]: ...

    def set_status(
        self,
        document_id: str,
        status: NormativeDocumentStatus,
        *,
        replace_active_versions: bool = False,
    ) -> NormativeDocument: ...

    def delete_document(self, document_id: str) -> NormativeDocument: ...


class PDFTextExtractorPort(Protocol):
    """Adaptador intercambiable para PDF digitales u OCR."""

    def extract(self, pdf_bytes: bytes) -> list[PDFPage]: ...


class LegalDocumentChunkerPort(Protocol):
    """Convierte páginas en unidades jurídicas recuperables."""

    def chunk(self, pages: list[PDFPage]) -> list[LegalSection]: ...
