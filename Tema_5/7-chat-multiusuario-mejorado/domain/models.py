"""Modelos del dominio del chat.

Esta es la capa más estable del proyecto. Sus clases describen usuarios,
conversaciones, mensajes y recuerdos sin conocer cómo se dibuja la interfaz o
qué proveedor ejecuta el modelo. Esa independencia es la base de una
arquitectura por capas: cambiar Streamlit no obliga a cambiar estos modelos.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Devuelve una fecha UTC comparable y serializable por SQLite/JSON."""

    return datetime.now(timezone.utc).isoformat()


# 1. Entidades persistentes de la aplicación.
@dataclass(frozen=True, slots=True)
class User:
    """Persona que posee sus propios chats y recuerdos."""

    user_id: str
    display_name: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Chat:
    """Metadatos de una conversación; los mensajes viven en LangGraph."""

    chat_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    turn_count: int


MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Representación simple que la capa de UI sabe mostrar."""

    role: MessageRole
    content: str
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """Recuerdo durable recuperado del almacén de largo plazo."""

    key: str
    content: str
    category: str
    importance: int
    updated_at: str


@dataclass(frozen=True, slots=True)
class AgentReply:
    """Resultado del agente más avisos no fatales del guardado de memoria."""

    content: str
    memories_saved: int = 0
    warning: str | None = None


# 2. Contexto de ejecución del agente.
#
# ``user_id`` no se escribe dentro del prompt. LangChain lo entrega de forma
# tipada a las herramientas, evitando que el modelo pueda escoger la memoria de
# otro usuario mediante una instrucción maliciosa.
@dataclass(frozen=True, slots=True)
class AgentContext:
    """Datos confiables que la aplicación entrega al agente en cada llamada."""

    user_id: str
    # Estos recuerdos se recuperan UNA vez antes de entrar al bucle del agente.
    # Así, si el agente usa una herramienta y vuelve a consultar al modelo, no
    # se repite innecesariamente la llamada de embeddings.
    relevant_memories: tuple[str, ...] = ()
    # La evidencia normativa es global y ya llega filtrada por vigencia. Cada
    # bloque contiene procedencia para que la respuesta pueda citarla.
    relevant_norms: tuple[str, ...] = ()


# 3. Salida estructurada del extractor de recuerdos.
#
# A diferencia del tutorial original, el resultado contiene una LISTA. Por eso
# una frase como "me llamo Ana, vivo en Yopal y trabajo en una alcaldía" puede
# generar tres recuerdos en un solo turno.
MemoryCategory = Literal[
    "personal",
    "profesional",
    "preferencias",
    "hechos_importantes",
]


class MemoryFact(BaseModel):
    """Hecho estable que merece recordarse entre conversaciones."""

    # La clave describe un espacio semántico estable. Si el usuario cambia de
    # empleo, ``profesional.empleo`` se sobrescribe en lugar de duplicarse.
    key: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[a-z0-9][a-z0-9_.-]+$",
        description="Clave estable, por ejemplo personal.nombre.",
    )
    content: str = Field(
        min_length=3,
        max_length=500,
        description="Hecho autocontenido redactado en tercera persona.",
    )
    category: MemoryCategory
    importance: int = Field(ge=1, le=5)


class MemoryBatch(BaseModel):
    """Cero o varios recuerdos extraídos de un mensaje del usuario."""

    facts: list[MemoryFact] = Field(default_factory=list, max_length=10)


# 4. Modelos de la base normativa global.
#
# Estos modelos no contienen ``user_id`` porque una norma publicada pertenece
# al conocimiento común del asistente. La memoria personal continúa aislada en
# ``MemoryRecord`` y nunca se mezcla físicamente con estos documentos.
NormativeDocumentStatus = Literal[
    "draft",
    "active",
    "superseded",
    "repealed",
]


@dataclass(frozen=True, slots=True)
class PDFPage:
    """Texto extraído de una página y su número visible para las citas."""

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class LegalSection:
    """Unidad jurídica detectada antes de asignarle persistencia."""

    article: str
    heading: str
    page_start: int
    page_end: int
    content: str


@dataclass(frozen=True, slots=True)
class NormativeDocument:
    """Versión auditable de una ley, decreto, resolución u otra norma."""

    document_id: str
    logical_key: str
    title: str
    norm_type: str
    norm_number: str
    norm_year: int | None
    jurisdiction: str
    version_label: str
    source_url: str
    status: NormativeDocumentStatus
    effective_from: str | None
    effective_to: str | None
    supersedes_document_id: str | None
    superseded_by_document_id: str | None
    checksum_sha256: str
    original_filename: str
    stored_path: str
    chunk_count: int
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class NormativeChunk:
    """Fragmento jurídico que conserva su artículo y páginas de origen."""

    chunk_id: str
    document_id: str
    position: int
    article: str
    heading: str
    page_start: int
    page_end: int
    content: str


@dataclass(frozen=True, slots=True)
class NormativeSearchResult:
    """Evidencia recuperada que el agente puede citar en una respuesta."""

    chunk_id: str
    document_id: str
    content: str
    citation: str
    source_url: str
    article: str
    score: float

    def prompt_block(self) -> str:
        """Formatea evidencia y procedencia sin convertirlas en instrucciones."""

        source = self.source_url or "Fuente cargada por el administrador"
        return (
            f"Cita: {self.citation}\n"
            f"Fuente: {source}\n"
            f"Contenido:\n{self.content}"
        )


# 5. Errores de dominio legibles por la capa de presentación.
class DomainError(Exception):
    """Clase base para errores esperados que puede mostrar la interfaz."""


class ValidationError(DomainError):
    """La entrada del usuario no cumple una regla del sistema."""


class ResourceNotFoundError(DomainError):
    """El usuario o el chat solicitado no existe."""


class ExternalServiceError(DomainError):
    """Un proveedor externo no pudo completar una operación necesaria."""
