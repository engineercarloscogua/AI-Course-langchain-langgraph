"""Pruebas de la salida estructurada de memoria."""

import unittest

from pydantic import ValidationError as PydanticValidationError

from domain.models import MemoryBatch, MemoryFact


class MemoryModelsTests(unittest.TestCase):
    def test_one_message_can_hold_multiple_independent_facts(self) -> None:
        batch = MemoryBatch(
            facts=[
                MemoryFact(
                    key="personal.nombre",
                    content="El usuario se llama Carlos.",
                    category="personal",
                    importance=4,
                ),
                MemoryFact(
                    key="profesional.empleo",
                    content="El usuario trabaja en una alcaldía.",
                    category="profesional",
                    importance=4,
                ),
            ]
        )

        self.assertEqual(len(batch.facts), 2)
        self.assertEqual(batch.facts[1].key, "profesional.empleo")

    def test_memory_key_rejects_spaces_and_uppercase(self) -> None:
        with self.assertRaises(PydanticValidationError):
            MemoryFact(
                key="Nombre Personal",
                content="El usuario se llama Carlos.",
                category="personal",
                importance=3,
            )


if __name__ == "__main__":
    unittest.main()
