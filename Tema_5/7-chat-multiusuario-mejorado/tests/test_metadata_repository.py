"""Pruebas del repositorio SQLite sin usar OpenAI."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from infrastructure.metadata_repository import SQLiteMetadataRepository


class MetadataRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        path = Path(self._temporary_directory.name) / "metadata.sqlite3"
        self.repository = SQLiteMetadataRepository(path)

    def tearDown(self) -> None:
        self.repository.close()
        self._temporary_directory.cleanup()

    def test_users_cannot_read_each_others_chats(self) -> None:
        first_user = self.repository.create_user("Ana")
        second_user = self.repository.create_user("Luis")
        chat = self.repository.create_chat(first_user.user_id)

        self.assertIsNotNone(self.repository.get_chat(first_user.user_id, chat.chat_id))
        self.assertIsNone(self.repository.get_chat(second_user.user_id, chat.chat_id))

    def test_first_turn_updates_title_and_counter(self) -> None:
        user = self.repository.create_user("Ana")
        chat = self.repository.create_chat(user.user_id)

        updated = self.repository.record_turn(
            user.user_id,
            chat.chat_id,
            "Estoy construyendo un agente para mi curso",
        )

        self.assertEqual(updated.turn_count, 1)
        self.assertEqual(updated.title, "Estoy construyendo un agente para mi curso")

    def test_data_remains_after_reopening_database(self) -> None:
        user = self.repository.create_user("Ana")
        database_path = Path(self._temporary_directory.name) / "metadata.sqlite3"
        self.repository.close()

        self.repository = SQLiteMetadataRepository(database_path)

        loaded = self.repository.get_user(user.user_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.display_name, "Ana")


if __name__ == "__main__":
    unittest.main()
