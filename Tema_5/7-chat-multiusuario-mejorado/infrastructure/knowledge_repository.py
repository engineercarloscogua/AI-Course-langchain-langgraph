"""Catálogo versionado e índice vectorial de conocimiento normativo.

SQLite conserva el documento completo, sus versiones y cada fragmento para
auditoría. ``SqliteStore`` mantiene únicamente los fragmentos publicados en el
índice semántico. Una norma desactivada se conserva en el catálogo, pero queda
fuera de las respuestas actuales.
"""

from collections.abc import Iterable
from datetime import date
from pathlib import Path
import re
import sqlite3
from threading import RLock
from typing import cast

from langchain_core.embeddings import Embeddings
from langgraph.store.sqlite import SqliteStore

from domain.models import (
    NormativeChunk,
    NormativeDocument,
    NormativeDocumentStatus,
    NormativeSearchResult,
    ResourceNotFoundError,
    ValidationError,
    utc_now_iso,
)


KNOWLEDGE_NAMESPACE = ("knowledge", "traffic_regulations")
VALID_STATUSES = {"draft", "active", "superseded", "repealed"}


class SQLiteKnowledgeRepository:
    """Implementa catálogo, búsqueda textual e índice vectorial en un archivo."""

    def __init__(
        self,
        database_path: Path | str,
        embeddings: Embeddings,
        embedding_dimensions: int,
        max_results: int,
    ):
        self._max_results = max_results
        self._lock = RLock()
        self._connection = sqlite3.connect(
            str(database_path),
            check_same_thread=False,
            isolation_level=None,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")

        # El Store se dedica exclusivamente a similitud semántica. La tabla SQL
        # definida abajo sigue siendo la fuente de verdad para vigencia y citas.
        self._store = SqliteStore(
            self._connection,
            index={
                "embed": embeddings,
                "dims": embedding_dimensions,
                "fields": ["content"],
            },
        )
        self._store.setup()
        self._setup_schema()

    def _setup_schema(self) -> None:
        """Crea tablas idempotentes y una búsqueda textual complementaria."""

        with self._lock:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS normative_documents (
                    document_id TEXT PRIMARY KEY,
                    logical_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    norm_type TEXT NOT NULL,
                    norm_number TEXT NOT NULL,
                    norm_year INTEGER,
                    jurisdiction TEXT NOT NULL,
                    version_label TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (
                        status IN ('draft', 'active', 'superseded', 'repealed')
                    ),
                    effective_from TEXT,
                    effective_to TEXT,
                    supersedes_document_id TEXT,
                    superseded_by_document_id TEXT,
                    checksum_sha256 TEXT NOT NULL UNIQUE,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (supersedes_document_id)
                        REFERENCES normative_documents(document_id),
                    FOREIGN KEY (superseded_by_document_id)
                        REFERENCES normative_documents(document_id)
                );

                CREATE INDEX IF NOT EXISTS idx_normative_documents_logical_key
                    ON normative_documents(logical_key, status);

                CREATE TABLE IF NOT EXISTS normative_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    article TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    page_start INTEGER NOT NULL,
                    page_end INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    UNIQUE(document_id, position),
                    FOREIGN KEY (document_id)
                        REFERENCES normative_documents(document_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_normative_chunks_document
                    ON normative_chunks(document_id, position);

                CREATE VIRTUAL TABLE IF NOT EXISTS normative_chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    document_id UNINDEXED,
                    article,
                    heading,
                    content,
                    tokenize='unicode61 remove_diacritics 2'
                );
                """
            )

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> NormativeDocument:
        return NormativeDocument(
            document_id=row["document_id"],
            logical_key=row["logical_key"],
            title=row["title"],
            norm_type=row["norm_type"],
            norm_number=row["norm_number"],
            norm_year=row["norm_year"],
            jurisdiction=row["jurisdiction"],
            version_label=row["version_label"],
            source_url=row["source_url"],
            status=cast(NormativeDocumentStatus, row["status"]),
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
            supersedes_document_id=row["supersedes_document_id"],
            superseded_by_document_id=row["superseded_by_document_id"],
            checksum_sha256=row["checksum_sha256"],
            original_filename=row["original_filename"],
            stored_path=row["stored_path"],
            chunk_count=row["chunk_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _chunk_from_row(row: sqlite3.Row) -> NormativeChunk:
        return NormativeChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            position=row["position"],
            article=row["article"],
            heading=row["heading"],
            page_start=row["page_start"],
            page_end=row["page_end"],
            content=row["content"],
        )

    def add_document(
        self,
        document: NormativeDocument,
        chunks: list[NormativeChunk],
    ) -> None:
        """Guarda una versión como borrador antes de intentar vectorizarla."""

        if document.status != "draft":
            raise ValidationError("Todo documento nuevo debe ingresar como borrador.")
        if not chunks:
            raise ValidationError("El documento debe contener al menos un fragmento.")
        if any(chunk.document_id != document.document_id for chunk in chunks):
            raise ValidationError("Los fragmentos no pertenecen al documento indicado.")

        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                self._connection.execute(
                    """
                    INSERT INTO normative_documents (
                        document_id, logical_key, title, norm_type, norm_number,
                        norm_year, jurisdiction, version_label, source_url,
                        status, effective_from, effective_to,
                        supersedes_document_id, superseded_by_document_id,
                        checksum_sha256, original_filename, stored_path,
                        chunk_count, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document.document_id,
                        document.logical_key,
                        document.title,
                        document.norm_type,
                        document.norm_number,
                        document.norm_year,
                        document.jurisdiction,
                        document.version_label,
                        document.source_url,
                        document.status,
                        document.effective_from,
                        document.effective_to,
                        document.supersedes_document_id,
                        document.superseded_by_document_id,
                        document.checksum_sha256,
                        document.original_filename,
                        document.stored_path,
                        len(chunks),
                        document.created_at,
                        document.updated_at,
                    ),
                )
                for chunk in chunks:
                    self._connection.execute(
                        """
                        INSERT INTO normative_chunks (
                            chunk_id, document_id, position, article, heading,
                            page_start, page_end, content
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.position,
                            chunk.article,
                            chunk.heading,
                            chunk.page_start,
                            chunk.page_end,
                            chunk.content,
                        ),
                    )
                    self._connection.execute(
                        """
                        INSERT INTO normative_chunks_fts (
                            chunk_id, document_id, article, heading, content
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.article,
                            chunk.heading,
                            chunk.content,
                        ),
                    )
                self._connection.commit()
            except sqlite3.IntegrityError as error:
                self._connection.rollback()
                if "checksum_sha256" in str(error):
                    raise ValidationError("Este mismo PDF ya fue cargado.") from error
                raise
            except Exception:
                self._connection.rollback()
                raise

    def get_document(self, document_id: str) -> NormativeDocument | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM normative_documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        return self._document_from_row(row) if row else None

    def find_by_checksum(self, checksum_sha256: str) -> NormativeDocument | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM normative_documents WHERE checksum_sha256 = ?",
                (checksum_sha256,),
            ).fetchone()
        return self._document_from_row(row) if row else None

    def list_documents(self) -> list[NormativeDocument]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM normative_documents
                ORDER BY created_at DESC, title COLLATE NOCASE
                """
            ).fetchall()
        return [self._document_from_row(row) for row in rows]

    def _chunks_for_document(self, document_id: str) -> list[NormativeChunk]:
        rows = self._connection.execute(
            """
            SELECT * FROM normative_chunks
            WHERE document_id = ?
            ORDER BY position
            """,
            (document_id,),
        ).fetchall()
        return [self._chunk_from_row(row) for row in rows]

    @staticmethod
    def _citation(document: NormativeDocument, chunk: NormativeChunk) -> str:
        pages = (
            f"página {chunk.page_start}"
            if chunk.page_start == chunk.page_end
            else f"páginas {chunk.page_start}-{chunk.page_end}"
        )
        version = f", versión {document.version_label}" if document.version_label else ""
        return f"{document.title}, {chunk.article}{version}, {pages}"

    def _index_document(self, document: NormativeDocument) -> None:
        """Vectoriza una versión completa y revierte elementos parciales al fallar."""

        with self._lock:
            chunks = self._chunks_for_document(document.document_id)
            indexed: list[str] = []
            try:
                for chunk in chunks:
                    self._store.put(
                        KNOWLEDGE_NAMESPACE,
                        chunk.chunk_id,
                        {
                            "chunk_id": chunk.chunk_id,
                            "document_id": document.document_id,
                            "content": chunk.content,
                            "article": chunk.article,
                            "citation": self._citation(document, chunk),
                            "source_url": document.source_url,
                        },
                        index=["content"],
                    )
                    indexed.append(chunk.chunk_id)
            except Exception:
                for chunk_id in indexed:
                    try:
                        self._store.delete(KNOWLEDGE_NAMESPACE, chunk_id)
                    except Exception:
                        pass
                raise

    def _deindex_documents(self, document_ids: Iterable[str]) -> None:
        """Retira vectores; el catálogo ya impide usar cualquier residuo obsoleto."""

        with self._lock:
            for document_id in document_ids:
                for chunk in self._chunks_for_document(document_id):
                    try:
                        self._store.delete(KNOWLEDGE_NAMESPACE, chunk.chunk_id)
                    except Exception:
                        # La vigencia se valida nuevamente contra SQL al buscar.
                        # Un fallo de limpieza no puede reactivar una norma vieja.
                        pass

    def _deindex_chunk_ids(self, chunk_ids: Iterable[str]) -> None:
        """Elimina claves conocidas cuando el catálogo ya no conserva sus filas."""

        with self._lock:
            for chunk_id in chunk_ids:
                try:
                    self._store.delete(KNOWLEDGE_NAMESPACE, chunk_id)
                except Exception:
                    pass

    def set_status(
        self,
        document_id: str,
        status: NormativeDocumentStatus,
        *,
        replace_active_versions: bool = False,
    ) -> NormativeDocument:
        """Publica o retira una versión conservando el historial jurídico."""

        if status not in VALID_STATUSES:
            raise ValidationError("El estado normativo no es válido.")
        document = self.get_document(document_id)
        if document is None:
            raise ResourceNotFoundError("El documento normativo no existe.")
        if document.status == status and not (
            status == "active" and replace_active_versions
        ):
            return document

        previous_active_ids: list[str] = []
        if status == "active":
            # Primero se vectoriza. Si OpenAI falla, el documento sigue siendo
            # borrador y la versión vigente anterior permanece disponible.
            self._index_document(document)

        now = utc_now_iso()
        today = date.today().isoformat()
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                if status == "active" and replace_active_versions:
                    rows = self._connection.execute(
                        """
                        SELECT document_id FROM normative_documents
                        WHERE logical_key = ? AND status = 'active'
                          AND document_id <> ?
                        ORDER BY updated_at DESC
                        """,
                        (document.logical_key, document_id),
                    ).fetchall()
                    previous_active_ids = [row["document_id"] for row in rows]
                    self._connection.execute(
                        """
                        UPDATE normative_documents
                        SET status = 'superseded',
                            effective_to = COALESCE(effective_to, ?),
                            superseded_by_document_id = ?,
                            updated_at = ?
                        WHERE logical_key = ? AND status = 'active'
                          AND document_id <> ?
                        """,
                        (today, document_id, now, document.logical_key, document_id),
                    )

                self._connection.execute(
                    """
                    UPDATE normative_documents
                    SET status = ?, updated_at = ?,
                        supersedes_document_id = COALESCE(
                            supersedes_document_id, ?
                        )
                    WHERE document_id = ?
                    """,
                    (
                        status,
                        now,
                        previous_active_ids[0] if previous_active_ids else None,
                        document_id,
                    ),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                if status == "active":
                    self._deindex_documents([document_id])
                raise

        if document.status == "active" and status != "active":
            self._deindex_documents([document_id])
        if previous_active_ids:
            self._deindex_documents(previous_active_ids)

        updated = self.get_document(document_id)
        if updated is None:  # pragma: no cover - defensa ante corrupción externa
            raise ResourceNotFoundError("El documento desapareció durante la actualización.")
        return updated

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        """Prepara términos seguros para FTS5 sin aceptar operadores externos."""

        ignored = {
            "para", "como", "cual", "cuál", "donde", "desde", "esta",
            "este", "estos", "estas", "sobre", "segun", "según", "una",
            "uno", "unos", "unas", "del", "las", "los", "que", "por",
            "con", "sin", "sus", "son", "hay",
        }
        terms: list[str] = []
        for term in re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+", query.casefold()):
            if len(term) < 2 or term in ignored or term in terms:
                continue
            terms.append(term)
            if len(terms) == 16:
                break
        return terms

    def _lexical_chunk_ids(self, query: str, limit: int) -> list[str]:
        terms = self._query_terms(query)
        if not terms:
            return []
        expression = " OR ".join(f'"{term}"' for term in terms)
        today = date.today().isoformat()
        with self._lock:
            try:
                rows = self._connection.execute(
                    """
                    SELECT f.chunk_id, bm25(normative_chunks_fts) AS relevance
                    FROM normative_chunks_fts AS f
                    JOIN normative_documents AS d ON d.document_id = f.document_id
                    WHERE normative_chunks_fts MATCH ?
                      AND d.status = 'active'
                      AND (d.effective_from IS NULL OR d.effective_from <= ?)
                      AND (d.effective_to IS NULL OR d.effective_to >= ?)
                    ORDER BY relevance
                    LIMIT ?
                    """,
                    (expression, today, today, limit),
                ).fetchall()
                return [row["chunk_id"] for row in rows]
            except sqlite3.OperationalError:
                # Respaldo para compilaciones excepcionales de SQLite sin FTS5.
                rows = self._connection.execute(
                    """
                    SELECT c.chunk_id, c.article, c.heading, c.content
                    FROM normative_chunks AS c
                    JOIN normative_documents AS d USING(document_id)
                    WHERE d.status = 'active'
                      AND (d.effective_from IS NULL OR d.effective_from <= ?)
                      AND (d.effective_to IS NULL OR d.effective_to >= ?)
                    """,
                    (today, today),
                ).fetchall()
        ranked = sorted(
            rows,
            key=lambda row: sum(
                term in f"{row['article']} {row['heading']} {row['content']}".casefold()
                for term in terms
            ),
            reverse=True,
        )
        return [row["chunk_id"] for row in ranked[:limit]]

    def _active_result(self, chunk_id: str, score: float) -> NormativeSearchResult | None:
        today = date.today().isoformat()
        with self._lock:
            row = self._connection.execute(
                """
                SELECT c.*, d.*
                FROM normative_chunks AS c
                JOIN normative_documents AS d USING(document_id)
                WHERE c.chunk_id = ? AND d.status = 'active'
                  AND (d.effective_from IS NULL OR d.effective_from <= ?)
                  AND (d.effective_to IS NULL OR d.effective_to >= ?)
                """,
                (chunk_id, today, today),
            ).fetchone()
        if row is None:
            return None
        document = self._document_from_row(row)
        chunk = self._chunk_from_row(row)
        return NormativeSearchResult(
            chunk_id=chunk.chunk_id,
            document_id=document.document_id,
            content=chunk.content,
            citation=self._citation(document, chunk),
            source_url=document.source_url,
            article=chunk.article,
            score=score,
        )

    def search(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[NormativeSearchResult]:
        """Combina similitud semántica y coincidencias exactas mediante RRF."""

        clean_query = query.strip()
        if not clean_query:
            return []
        today = date.today().isoformat()
        with self._lock:
            active_count = self._connection.execute(
                """
                SELECT COUNT(*) FROM normative_documents
                WHERE status = 'active'
                  AND (effective_from IS NULL OR effective_from <= ?)
                  AND (effective_to IS NULL OR effective_to >= ?)
                """,
                (today, today),
            ).fetchone()[0]
        if not active_count:
            # Evita pagar/generar un embedding cuando el administrador todavía
            # no ha publicado ninguna norma vigente.
            return []
        result_limit = max(1, min(limit or self._max_results, 20))
        candidate_limit = max(result_limit * 5, 20)

        vector_ids: list[str] = []
        try:
            with self._lock:
                vector_items = self._store.search(
                    KNOWLEDGE_NAMESPACE,
                    query=clean_query,
                    limit=candidate_limit,
                )
            vector_ids = [item.key for item in vector_items]
        except Exception:
            # La consulta textual sigue funcionando si embeddings no responde.
            vector_ids = []

        lexical_ids = self._lexical_chunk_ids(clean_query, candidate_limit)
        scores: dict[str, float] = {}
        for rank, chunk_id in enumerate(vector_ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (60 + rank)
        for rank, chunk_id in enumerate(lexical_ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (60 + rank)

        results: list[NormativeSearchResult] = []
        for chunk_id, score in sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            result = self._active_result(chunk_id, score)
            if result is not None:
                results.append(result)
            if len(results) == result_limit:
                break
        return results

    def delete_document(self, document_id: str) -> NormativeDocument:
        """Elimina catálogo y texto; el servicio se ocupa del PDF original."""

        document = self.get_document(document_id)
        if document is None:
            raise ResourceNotFoundError("El documento normativo no existe.")

        with self._lock:
            chunk_ids = [
                chunk.chunk_id for chunk in self._chunks_for_document(document_id)
            ]
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                self._connection.execute(
                    "DELETE FROM normative_chunks_fts WHERE document_id = ?",
                    (document_id,),
                )
                # Las relaciones históricas se conservan mientras ambas
                # versiones existen. Al borrar una de forma permanente se
                # limpian para respetar las claves foráneas del catálogo.
                self._connection.execute(
                    """
                    UPDATE normative_documents
                    SET supersedes_document_id = NULL
                    WHERE supersedes_document_id = ?
                    """,
                    (document_id,),
                )
                self._connection.execute(
                    """
                    UPDATE normative_documents
                    SET superseded_by_document_id = NULL
                    WHERE superseded_by_document_id = ?
                    """,
                    (document_id,),
                )
                self._connection.execute(
                    "DELETE FROM normative_documents WHERE document_id = ?",
                    (document_id,),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
        self._deindex_chunk_ids(chunk_ids)
        return document

    def close(self) -> None:
        with self._lock:
            self._connection.close()
