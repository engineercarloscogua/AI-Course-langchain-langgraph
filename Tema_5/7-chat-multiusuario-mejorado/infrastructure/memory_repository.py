"""Repositorio de memoria de largo plazo sobre LangGraph Store.

El Store y el checkpointer resuelven problemas diferentes:

* el checkpointer conserva los mensajes de UN hilo de conversación;
* este repositorio conserva hechos del USUARIO y los comparte entre sus hilos.

La separación hace explícito por qué un dato personal sigue disponible al
crear un chat nuevo o al reiniciar Streamlit.
"""

import re
from typing import Any

from langgraph.store.base import BaseStore, Item

from domain.models import MemoryFact, MemoryRecord


def memory_namespace(user_id: str) -> tuple[str, str]:
    """Construye el espacio aislado que pertenece a un usuario."""

    return (user_id, "memories")


def _terms(text: str) -> set[str]:
    """Tokenizador pequeño usado únicamente como respaldo sin embeddings."""

    return set(re.findall(r"\w+", text.casefold(), flags=re.UNICODE))


def safe_memory_search(
    store: BaseStore,
    user_id: str,
    query: str,
    limit: int,
) -> list[Item]:
    """Busca semánticamente y cae a una búsqueda local si falla la red.

    Los embeddings de OpenAI producen la búsqueda de mejor calidad, pero una
    caída temporal de esa API no debería impedir que el agente responda. En tal
    caso se leen recuerdos recientes y se ordenan por palabras compartidas.
    """

    namespace = memory_namespace(user_id)
    try:
        return store.search(namespace, query=query, limit=limit)
    except Exception:
        candidates = store.search(namespace, limit=100)
        query_terms = _terms(query)
        return sorted(
            candidates,
            key=lambda item: len(query_terms & _terms(str(item.value.get("content", "")))),
            reverse=True,
        )[:limit]


class LongTermMemoryRepository:
    """Guarda, consulta y elimina recuerdos aislados por usuario."""

    def __init__(self, store: BaseStore, max_results: int):
        self._store = store
        self._max_results = max_results

    @staticmethod
    def _to_record(item: Item) -> MemoryRecord:
        """Traduce el tipo externo de LangGraph a un tipo del dominio."""

        value: dict[str, Any] = item.value
        return MemoryRecord(
            key=item.key,
            content=str(value.get("content", "")),
            category=str(value.get("category", "hechos_importantes")),
            importance=int(value.get("importance", 1)),
            updated_at=str(item.updated_at),
        )

    def save_many(self, user_id: str, facts: list[MemoryFact], source: str) -> int:
        """Guarda todos los hechos y reemplaza los que tengan la misma clave."""

        namespace = memory_namespace(user_id)
        saved = 0
        for fact in facts:
            self._store.put(
                namespace,
                fact.key,
                {
                    "content": fact.content,
                    "category": fact.category,
                    "importance": fact.importance,
                    "source": source[:1_000],
                },
                # Solo el contenido aporta significado a la búsqueda vectorial;
                # categoría e importancia se conservan como metadatos.
                index=["content"],
            )
            saved += 1
        return saved

    def search(self, user_id: str, query: str) -> list[MemoryRecord]:
        """Devuelve recuerdos relevantes para personalizar un turno."""

        items = safe_memory_search(
            self._store,
            user_id,
            query,
            self._max_results,
        )
        return [self._to_record(item) for item in items]

    def list_all(self, user_id: str) -> list[MemoryRecord]:
        """Lista los recuerdos para que el usuario pueda auditarlos."""

        items = self._store.search(memory_namespace(user_id), limit=1_000)
        records = [self._to_record(item) for item in items]
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def delete(self, user_id: str, memory_key: str) -> None:
        """Elimina un recuerdo concreto dentro del espacio del usuario."""

        self._store.delete(memory_namespace(user_id), memory_key)
