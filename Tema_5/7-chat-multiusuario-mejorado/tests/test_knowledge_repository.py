"""Pruebas del RAG normativo con embeddings deterministas y sin red."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from langchain_core.embeddings import DeterministicFakeEmbedding

from domain.models import NormativeChunk, NormativeDocument, utc_now_iso
from infrastructure.knowledge_repository import SQLiteKnowledgeRepository


class KnowledgeRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        database_path = Path(self._temporary_directory.name) / "knowledge.sqlite3"
        self.repository = SQLiteKnowledgeRepository(
            database_path=database_path,
            embeddings=DeterministicFakeEmbedding(size=8),
            embedding_dimensions=8,
            max_results=5,
        )

    def tearDown(self) -> None:
        self.repository.close()
        self._temporary_directory.cleanup()

    @staticmethod
    def _document(identifier: str, version: str, checksum: str) -> NormativeDocument:
        now = utc_now_iso()
        return NormativeDocument(
            document_id=identifier,
            logical_key="colombia-ley-999-2026",
            title="Ley 999 de 2026",
            norm_type="Ley",
            norm_number="999",
            norm_year=2026,
            jurisdiction="Colombia",
            version_label=version,
            source_url="https://example.gov.co/ley-999",
            status="draft",
            effective_from="2026-01-01",
            effective_to=None,
            supersedes_document_id=None,
            superseded_by_document_id=None,
            checksum_sha256=checksum,
            original_filename=f"{identifier}.pdf",
            stored_path=f"{identifier}.pdf",
            chunk_count=1,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _chunk(identifier: str, content: str) -> NormativeChunk:
        return NormativeChunk(
            chunk_id=f"{identifier}:00001",
            document_id=identifier,
            position=1,
            article="ARTÍCULO 10",
            heading="VELOCIDAD",
            page_start=2,
            page_end=2,
            content=content,
        )

    def test_only_current_version_is_returned_after_replacement(self) -> None:
        old = self._document("old", "Versión inicial", "a" * 64)
        self.repository.add_document(
            old,
            [self._chunk("old", "La velocidad máxima es 80 kilómetros por hora.")],
        )
        self.repository.set_status("old", "active")

        new = self._document("new", "Versión actualizada", "b" * 64)
        self.repository.add_document(
            new,
            [self._chunk("new", "La velocidad máxima vigente es 50 kilómetros por hora.")],
        )
        self.repository.set_status(
            "new",
            "active",
            replace_active_versions=True,
        )

        results = self.repository.search("velocidad máxima vigente")

        self.assertEqual(self.repository.get_document("old").status, "superseded")
        self.assertEqual(self.repository.get_document("new").status, "active")
        self.assertTrue(results)
        self.assertTrue(all(result.document_id == "new" for result in results))
        self.assertIn("ARTÍCULO 10", results[0].citation)

    def test_deactivated_document_remains_auditable_but_not_retrievable(self) -> None:
        document = self._document("doc", "Versión única", "c" * 64)
        self.repository.add_document(
            document,
            [self._chunk("doc", "Los conductores deben respetar la señalización.")],
        )
        self.repository.set_status("doc", "active")
        self.repository.set_status("doc", "repealed")

        self.assertEqual(self.repository.get_document("doc").status, "repealed")
        self.assertEqual(self.repository.search("señalización conductores"), [])

    def test_permanent_delete_removes_catalog_entry(self) -> None:
        document = self._document("draft", "Borrador", "d" * 64)
        self.repository.add_document(
            document,
            [self._chunk("draft", "Texto cargado por error.")],
        )

        self.repository.delete_document("draft")

        self.assertIsNone(self.repository.get_document("draft"))


if __name__ == "__main__":
    unittest.main()
