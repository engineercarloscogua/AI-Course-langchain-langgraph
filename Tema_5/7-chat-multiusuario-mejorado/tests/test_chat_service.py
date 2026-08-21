"""Pruebas de casos de uso mediante un agente falso y determinista."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from application.chat_service import ChatApplicationService
from domain.models import (
    AgentReply,
    ChatMessage,
    ExternalServiceError,
    MemoryRecord,
    ValidationError,
)
from infrastructure.metadata_repository import SQLiteMetadataRepository


class FakeAgentGateway:
    """Doble de prueba: implementa el puerto sin red, modelo ni embeddings."""

    def __init__(self) -> None:
        self.messages: dict[tuple[str, str], list[ChatMessage]] = {}
        self.deleted_threads: list[tuple[str, str]] = []

    def reply(self, user_id: str, chat_id: str, message: str) -> AgentReply:
        thread = self.messages.setdefault((user_id, chat_id), [])
        thread.extend(
            [
                ChatMessage(role="user", content=message),
                ChatMessage(role="assistant", content=f"Respuesta a: {message}"),
            ]
        )
        return AgentReply(content=f"Respuesta a: {message}", memories_saved=2)

    def history(self, user_id: str, chat_id: str) -> list[ChatMessage]:
        return list(self.messages.get((user_id, chat_id), []))

    def delete_thread(self, user_id: str, chat_id: str) -> None:
        self.deleted_threads.append((user_id, chat_id))
        self.messages.pop((user_id, chat_id), None)

    def list_memories(self, user_id: str) -> list[MemoryRecord]:
        return []

    def delete_memory(self, user_id: str, memory_key: str) -> None:
        return None


class FailingAgentGateway(FakeAgentGateway):
    """Simula una caída definitiva del proveedor después de los reintentos."""

    def reply(self, user_id: str, chat_id: str, message: str) -> AgentReply:
        raise ExternalServiceError("OpenAI no está disponible.")


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        database_path = Path(self._temporary_directory.name) / "metadata.sqlite3"
        self.repository = SQLiteMetadataRepository(database_path)
        self.agent = FakeAgentGateway()
        self.service = ChatApplicationService(
            metadata=self.repository,
            agent=self.agent,
            max_input_characters=100,
        )

    def tearDown(self) -> None:
        self.repository.close()
        self._temporary_directory.cleanup()

    def test_successful_turn_is_persisted_once(self) -> None:
        user, chat = self.service.bootstrap()

        reply = self.service.send_message(user.user_id, chat.chat_id, "Hola")

        updated_chat = self.repository.get_chat(user.user_id, chat.chat_id)
        self.assertEqual(reply.memories_saved, 2)
        self.assertEqual(updated_chat.turn_count, 1)
        self.assertEqual(len(self.service.history(user.user_id, chat.chat_id)), 2)

    def test_blank_message_is_rejected_before_calling_agent(self) -> None:
        user, chat = self.service.bootstrap()

        with self.assertRaises(ValidationError):
            self.service.send_message(user.user_id, chat.chat_id, "   ")

        self.assertEqual(self.agent.messages, {})

    def test_deleting_chat_also_deletes_its_checkpoint(self) -> None:
        user, chat = self.service.bootstrap()

        self.service.delete_chat(user.user_id, chat.chat_id)

        self.assertEqual(self.agent.deleted_threads, [(user.user_id, chat.chat_id)])
        self.assertIsNone(self.repository.get_chat(user.user_id, chat.chat_id))

    def test_failed_model_call_is_not_counted_as_successful_turn(self) -> None:
        user, chat = self.service.bootstrap()
        failing_service = ChatApplicationService(
            metadata=self.repository,
            agent=FailingAgentGateway(),
            max_input_characters=100,
        )

        with self.assertRaises(ExternalServiceError):
            failing_service.send_message(user.user_id, chat.chat_id, "Hola")

        unchanged_chat = self.repository.get_chat(user.user_id, chat.chat_id)
        self.assertEqual(unchanged_chat.turn_count, 0)


if __name__ == "__main__":
    unittest.main()
