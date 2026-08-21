"""Pruebas de fragmentación jurídica sin archivos ni servicios externos."""

import unittest

from domain.models import PDFPage
from infrastructure.pdf_ingestion import LegalDocumentChunker


class LegalDocumentChunkerTests(unittest.TestCase):
    def test_articles_preserve_page_range_and_continuations(self) -> None:
        pages = [
            PDFPage(
                page_number=1,
                text=(
                    "LEY 999 DE 2026\nObjeto general.\n\n"
                    "ARTÍCULO 1°. OBJETO\nLa presente ley regula el tránsito."
                ),
            ),
            PDFPage(
                page_number=2,
                text=(
                    "Esta frase continúa el artículo anterior.\n\n"
                    "ARTÍCULO 2°. VELOCIDAD\nLa velocidad máxima será señalizada."
                ),
            ),
        ]

        sections = LegalDocumentChunker(max_characters=2_000).chunk(pages)

        articles = {section.article: section for section in sections}
        self.assertIn("Preámbulo y disposiciones iniciales", articles)
        self.assertIn("ARTÍCULO 1°", articles)
        self.assertIn("ARTÍCULO 2°", articles)
        self.assertEqual(articles["ARTÍCULO 1°"].page_start, 1)
        self.assertEqual(articles["ARTÍCULO 1°"].page_end, 2)
        self.assertIn("continúa", articles["ARTÍCULO 1°"].content)
        self.assertEqual(articles["ARTÍCULO 2°"].heading, "VELOCIDAD")

    def test_oversized_article_is_split_with_identity_in_every_part(self) -> None:
        pages = [
            PDFPage(
                page_number=4,
                text="ARTÍCULO 10. CONTENIDO\n" + ("regulación vial " * 200),
            )
        ]

        sections = LegalDocumentChunker(max_characters=1_000).chunk(pages)

        self.assertGreater(len(sections), 1)
        self.assertTrue(all(section.article == "ARTÍCULO 10" for section in sections))
        self.assertTrue(all("ARTÍCULO 10 · parte" in section.content for section in sections))


if __name__ == "__main__":
    unittest.main()
