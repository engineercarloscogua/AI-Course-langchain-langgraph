"""Pruebas de aislamiento y actualización de memoria sin usar OpenAI."""

import unittest

from langchain_core.embeddings import DeterministicFakeEmbedding
from langgraph.store.memory import InMemoryStore

from domain.models import MemoryFact
from infrastructure.memory_repository import LongTermMemoryRepository


def _fact(key: str, content: str) -> MemoryFact:
    """Crea un hecho válido y mantiene cada prueba concentrada en su regla."""

    return MemoryFact(
        key=key,
        content=content,
        category="personal",
        importance=4,
    )


class MemoryRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        # Los vectores deterministas ejercitan la búsqueda semántica sin red.
        store = InMemoryStore(
            index={
                "embed": DeterministicFakeEmbedding(size=8),
                "dims": 8,
                "fields": ["content"],
            }
        )
        self.repository = LongTermMemoryRepository(store, max_results=3)

    def test_same_semantic_key_updates_instead_of_duplicating(self) -> None:
        self.repository.save_many(
            "user-1",
            [_fact("personal.ubicacion", "El usuario vive en Bogotá.")],
            source="Vivo en Bogotá",
        )
        self.repository.save_many(
            "user-1",
            [_fact("personal.ubicacion", "El usuario vive en Yopal.")],
            source="Ahora vivo en Yopal",
        )

        memories = self.repository.list_all("user-1")

        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "El usuario vive en Yopal.")

    def test_namespaces_isolate_users(self) -> None:
        self.repository.save_many(
            "user-1",
            [_fact("personal.nombre", "El usuario se llama Ana.")],
            source="Me llamo Ana",
        )

        self.assertEqual(len(self.repository.list_all("user-1")), 1)
        self.assertEqual(self.repository.list_all("user-2"), [])


if __name__ == "__main__":
    unittest.main()
