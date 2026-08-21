"""Pruebas del caso de uso de carga, archivos y duplicados."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from langchain_core.embeddings import DeterministicFakeEmbedding

from application.knowledge_service import KnowledgeApplicationService, NormativeUpload
from domain.models import PDFPage, ValidationError
from infrastructure.knowledge_repository import SQLiteKnowledgeRepository
from infrastructure.pdf_ingestion import LegalDocumentChunker


class FakePDFExtractor:
    """Evita fabricar un PDF real; el parser tiene sus propias pruebas."""

    def extract(self, pdf_bytes: bytes) -> list[PDFPage]:
        return [
            PDFPage(
                page_number=1,
                text="ARTÍCULO 1°. OBJETO\nLa norma regula la movilidad segura.",
            )
        ]


class KnowledgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        base_path = Path(self._temporary_directory.name)
        self.repository = SQLiteKnowledgeRepository(
            database_path=base_path / "knowledge.sqlite3",
            embeddings=DeterministicFakeEmbedding(size=8),
            embedding_dimensions=8,
            max_results=5,
        )
        self.documents_path = base_path / "documents"
        self.service = KnowledgeApplicationService(
            repository=self.repository,
            extractor=FakePDFExtractor(),
            chunker=LegalDocumentChunker(max_characters=2_000),
            documents_directory=self.documents_path,
            max_pdf_bytes=2_000_000,
        )
        self.upload = NormativeUpload(
            filename="ley.pdf",
            content=b"%PDF-fake-for-isolated-service-test",
            title="Ley de movilidad segura",
            norm_type="Ley",
            norm_number="999",
            norm_year=2026,
            jurisdiction="Colombia",
            version_label="Primera versión",
            source_url="https://example.gov.co/ley-999",
            effective_from="2026-01-01",
            logical_key="colombia-ley-999-2026",
        )

    def tearDown(self) -> None:
        self.repository.close()
        self._temporary_directory.cleanup()

    def test_upload_can_remain_draft_without_vectorization(self) -> None:
        outcome = self.service.ingest_pdf(
            self.upload,
            publish=False,
            replace_active_versions=False,
        )

        self.assertEqual(outcome.document.status, "draft")
        self.assertEqual(outcome.document.chunk_count, 1)
        self.assertTrue(Path(outcome.document.stored_path).is_file())

    def test_duplicate_pdf_is_rejected(self) -> None:
        self.service.ingest_pdf(
            self.upload,
            publish=False,
            replace_active_versions=False,
        )

        with self.assertRaises(ValidationError):
            self.service.ingest_pdf(
                self.upload,
                publish=False,
                replace_active_versions=False,
            )


if __name__ == "__main__":
    unittest.main()
