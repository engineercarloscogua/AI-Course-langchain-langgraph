"""Casos de uso para administrar la base normativa compartida.

Streamlit entrega un archivo y metadatos a este servicio. Aquí se validan,
extraen y guardan; la presentación nunca conoce pypdf, SQLite ni embeddings.
"""

from dataclasses import dataclass
from datetime import date
import hashlib
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse
from uuid import uuid4
from typing import TypedDict

from domain.models import (
    ExternalServiceError,
    NormativeChunk,
    NormativeDocument,
    NormativeDocumentStatus,
    ValidationError,
    utc_now_iso,
)
from domain.ports import (
    LegalDocumentChunkerPort,
    NormativeKnowledgeRepositoryPort,
    PDFTextExtractorPort,
)


@dataclass(frozen=True, slots=True)
class NormativeUpload:
    """Datos capturados en el formulario administrativo."""

    filename: str
    content: bytes
    title: str
    norm_type: str
    norm_number: str = ""
    norm_year: int | None = None
    jurisdiction: str = "Colombia"
    version_label: str = ""
    source_url: str = ""
    effective_from: str | None = None
    effective_to: str | None = None
    logical_key: str = ""


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    """Resultado que diferencia una carga exitosa de una publicación fallida."""

    document: NormativeDocument
    warning: str | None = None


class _ValidatedUpload(TypedDict):
    """Forma normalizada que evita propagar valores ambiguos a las entidades."""

    filename: str
    title: str
    norm_type: str
    norm_number: str
    norm_year: int | None
    jurisdiction: str
    version_label: str
    source_url: str
    effective_from: str | None
    effective_to: str | None
    logical_key: str


class KnowledgeApplicationService:
    """Fachada administrativa de documentos jurídicos y sus versiones."""

    def __init__(
        self,
        repository: NormativeKnowledgeRepositoryPort,
        extractor: PDFTextExtractorPort,
        chunker: LegalDocumentChunkerPort,
        documents_directory: Path,
        max_pdf_bytes: int,
    ):
        self._repository = repository
        self._extractor = extractor
        self._chunker = chunker
        self._documents_directory = documents_directory
        self._documents_directory.mkdir(parents=True, exist_ok=True)
        self._max_pdf_bytes = max_pdf_bytes

    @staticmethod
    def _slug(value: str) -> str:
        """Convierte metadatos visibles en una clave estable y portable."""

        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")

    @staticmethod
    def _clean_date(value: str | None, field_name: str) -> str | None:
        clean = (value or "").strip()
        if not clean:
            return None
        try:
            return date.fromisoformat(clean).isoformat()
        except ValueError as error:
            raise ValidationError(
                f"{field_name} debe usar el formato AAAA-MM-DD."
            ) from error

    @staticmethod
    def _clean_url(value: str) -> str:
        clean = value.strip()
        if not clean:
            return ""
        parsed = urlparse(clean)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("La fuente oficial debe ser una URL http o https.")
        return clean

    def _validate(self, upload: NormativeUpload) -> _ValidatedUpload:
        """Normaliza entradas antes de escribir archivos o abrir el PDF."""

        filename = Path(upload.filename).name.strip()
        if not filename.casefold().endswith(".pdf"):
            raise ValidationError("Solo se permiten archivos PDF.")
        if not upload.content.startswith(b"%PDF-"):
            raise ValidationError("El archivo no tiene una cabecera PDF válida.")
        if not upload.content:
            raise ValidationError("El PDF está vacío.")
        if len(upload.content) > self._max_pdf_bytes:
            megabytes = self._max_pdf_bytes / (1024 * 1024)
            raise ValidationError(f"El PDF supera el límite de {megabytes:g} MB.")

        title = " ".join(upload.title.split())
        norm_type = " ".join(upload.norm_type.split())
        jurisdiction = " ".join(upload.jurisdiction.split())
        norm_number = " ".join(upload.norm_number.split())
        version_label = " ".join(upload.version_label.split())
        if len(title) < 5:
            raise ValidationError("Escribe un título normativo de al menos 5 caracteres.")
        if not norm_type:
            raise ValidationError("Selecciona o escribe el tipo de norma.")
        if not jurisdiction:
            raise ValidationError("La jurisdicción es obligatoria.")
        if upload.norm_year is not None:
            maximum_year = date.today().year + 1
            if not 1800 <= upload.norm_year <= maximum_year:
                raise ValidationError(
                    f"El año debe estar entre 1800 y {maximum_year}."
                )

        effective_from = self._clean_date(upload.effective_from, "Vigente desde")
        effective_to = self._clean_date(upload.effective_to, "Vigente hasta")
        if effective_from and effective_to and effective_to < effective_from:
            raise ValidationError(
                "La fecha final de vigencia no puede ser anterior a la inicial."
            )

        explicit_key = self._slug(upload.logical_key)
        automatic_key = self._slug(
            "-".join(
                part
                for part in (
                    jurisdiction,
                    norm_type,
                    norm_number,
                    str(upload.norm_year or ""),
                    title if not norm_number else "",
                )
                if part
            )
        )
        logical_key = explicit_key or automatic_key
        if len(logical_key) < 3:
            raise ValidationError("No fue posible construir una clave normativa válida.")

        return {
            "filename": filename,
            "title": title,
            "norm_type": norm_type,
            "norm_number": norm_number,
            "norm_year": upload.norm_year,
            "jurisdiction": jurisdiction,
            "version_label": version_label or f"Cargada {date.today().isoformat()}",
            "source_url": self._clean_url(upload.source_url),
            "effective_from": effective_from,
            "effective_to": effective_to,
            "logical_key": logical_key,
        }

    def ingest_pdf(
        self,
        upload: NormativeUpload,
        *,
        publish: bool,
        replace_active_versions: bool,
    ) -> IngestionOutcome:
        """Carga un PDF y opcionalmente publica su índice para todos los usuarios."""

        values = self._validate(upload)
        checksum = hashlib.sha256(upload.content).hexdigest()
        duplicate = self._repository.find_by_checksum(checksum)
        if duplicate is not None:
            raise ValidationError(
                f"Ese PDF ya está registrado como «{duplicate.title}» "
                f"({duplicate.version_label})."
            )

        pages = self._extractor.extract(upload.content)
        sections = self._chunker.chunk(pages)
        document_id = str(uuid4())
        stored_path = self._documents_directory / f"{document_id}.pdf"
        temporary_path = stored_path.with_suffix(".pdf.part")
        now = utc_now_iso()
        document = NormativeDocument(
            document_id=document_id,
            logical_key=str(values["logical_key"]),
            title=str(values["title"]),
            norm_type=str(values["norm_type"]),
            norm_number=str(values["norm_number"]),
            norm_year=values["norm_year"],
            jurisdiction=str(values["jurisdiction"]),
            version_label=str(values["version_label"]),
            source_url=str(values["source_url"]),
            status="draft",
            effective_from=values["effective_from"],
            effective_to=values["effective_to"],
            supersedes_document_id=None,
            superseded_by_document_id=None,
            checksum_sha256=checksum,
            original_filename=str(values["filename"]),
            stored_path=str(stored_path),
            chunk_count=len(sections),
            created_at=now,
            updated_at=now,
        )
        chunks = [
            NormativeChunk(
                chunk_id=f"{document_id}:{position:05d}",
                document_id=document_id,
                position=position,
                article=section.article,
                heading=section.heading,
                page_start=section.page_start,
                page_end=section.page_end,
                content=section.content,
            )
            for position, section in enumerate(sections, start=1)
        ]

        try:
            temporary_path.write_bytes(upload.content)
            temporary_path.replace(stored_path)
            self._repository.add_document(document, chunks)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            stored_path.unlink(missing_ok=True)
            raise

        if not publish:
            saved = self._repository.get_document(document_id)
            return IngestionOutcome(document=saved or document)

        try:
            published = self._repository.set_status(
                document_id,
                "active",
                replace_active_versions=replace_active_versions,
            )
            return IngestionOutcome(document=published)
        except Exception as error:
            saved = self._repository.get_document(document_id) or document
            return IngestionOutcome(
                document=saved,
                warning=(
                    "El PDF y sus fragmentos quedaron guardados como borrador, "
                    "pero no fue posible vectorizarlos. Puedes reintentar la "
                    f"publicación. Detalle: {type(error).__name__}: {error}"
                ),
            )

    def list_documents(self) -> list[NormativeDocument]:
        return self._repository.list_documents()

    def publish_document(
        self,
        document_id: str,
        *,
        replace_active_versions: bool,
    ) -> NormativeDocument:
        """Vectoriza un borrador y lo habilita para las respuestas del agente."""

        try:
            return self._repository.set_status(
                document_id,
                "active",
                replace_active_versions=replace_active_versions,
            )
        except (ValidationError, ExternalServiceError):
            raise
        except Exception as error:
            raise ExternalServiceError(
                "No fue posible publicar el documento. Verifica la conexión "
                f"con el servicio de embeddings. Detalle: {type(error).__name__}: {error}"
            ) from error

    def deactivate_document(
        self,
        document_id: str,
        status: NormativeDocumentStatus,
    ) -> NormativeDocument:
        """Retira una norma del RAG sin destruir su versión histórica."""

        if status not in {"draft", "superseded", "repealed"}:
            raise ValidationError("Selecciona un estado de retiro válido.")
        return self._repository.set_status(document_id, status)

    def delete_document_permanently(self, document_id: str) -> None:
        """Borra una versión de forma explícita, incluida su copia PDF."""

        document = self._repository.delete_document(document_id)
        Path(document.stored_path).unlink(missing_ok=True)
