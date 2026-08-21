"""Pruebas de la herramienta RAG sin invocar un modelo ni embeddings."""

import unittest

from agent.tools import build_agent_tools
from domain.models import NormativeSearchResult


class FakeKnowledgeSearch:
    def search(self, query: str, *, limit: int | None = None):
        if "velocidad" not in query.casefold():
            return []
        return [
            NormativeSearchResult(
                chunk_id="doc:1",
                document_id="doc",
                content="La velocidad será la indicada por la señal vigente.",
                citation="Ley 999 de 2026, ARTÍCULO 10, página 2",
                source_url="https://example.gov.co/ley-999",
                article="ARTÍCULO 10",
                score=1.0,
            )
        ]


class AgentToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = next(
            tool
            for tool in build_agent_tools(FakeKnowledgeSearch())
            if tool.name == "search_traffic_regulations"
        )

    def test_normative_tool_returns_content_and_traceable_source(self) -> None:
        output = self.tool.invoke({"query": "¿Cuál es la velocidad?"})

        self.assertIn("ARTÍCULO 10", output)
        self.assertIn("https://example.gov.co/ley-999", output)
        self.assertIn("señal vigente", output)

    def test_normative_tool_forbids_guessing_when_no_evidence_exists(self) -> None:
        output = self.tool.invoke({"query": "tema desconocido"})

        self.assertIn("No se encontró evidencia vigente", output)
        self.assertIn("No completes", output)


if __name__ == "__main__":
    unittest.main()
