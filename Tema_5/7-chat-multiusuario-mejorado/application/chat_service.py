"""Casos de uso de alto nivel consumidos por Streamlit.

La interfaz no llama directamente a SQL, LangGraph ni OpenAI. Solo expresa
intenciones como crear chat, enviar mensaje o borrar recuerdo. Este servicio
coordina los puertos y mantiene las reglas en un lugar reutilizable.
"""

from domain.models import (
    AgentReply,
    Chat,
    ChatMessage,
    MemoryRecord,
    ResourceNotFoundError,
    User,
    ValidationError,
)
from domain.ports import AgentGatewayPort, MetadataRepositoryPort


class ChatApplicationService:
    """Fachada de casos de uso del sistema multiusuario."""

    def __init__(
        self,
        metadata: MetadataRepositoryPort,
        agent: AgentGatewayPort,
        max_input_characters: int,
    ):
        self._metadata = metadata
        self._agent = agent
        self._max_input_characters = max_input_characters

    def bootstrap(self) -> tuple[User, Chat]:
        """Garantiza que el primer arranque tenga usuario y chat seleccionables."""

        user = self._metadata.ensure_default_user()
        chats = self._metadata.list_chats(user.user_id)
        chat = chats[0] if chats else self._metadata.create_chat(user.user_id)
        return user, chat

    def list_users(self) -> list[User]:
        return self._metadata.list_users()

    def create_user(self, display_name: str) -> tuple[User, Chat]:
        """Crea un usuario y su primera conversación como una sola operación."""

        user = self._metadata.create_user(display_name)
        return user, self._metadata.create_chat(user.user_id)

    def list_chats(self, user_id: str) -> list[Chat]:
        self._require_user(user_id)
        return self._metadata.list_chats(user_id)

    def create_chat(self, user_id: str) -> Chat:
        self._require_user(user_id)
        return self._metadata.create_chat(user_id)

    def send_message(self, user_id: str, chat_id: str, message: str) -> AgentReply:
        """Valida, conversa y registra el turno solo si hubo respuesta."""

        clean_message = message.strip()
        if not clean_message:
            raise ValidationError("Escribe un mensaje antes de enviarlo.")
        if len(clean_message) > self._max_input_characters:
            raise ValidationError(
                "El mensaje supera el límite de "
                f"{self._max_input_characters:,} caracteres."
            )

        self._require_chat(user_id, chat_id)
        result = self._agent.reply(user_id, chat_id, clean_message)
        self._metadata.record_turn(user_id, chat_id, clean_message)
        return result

    def history(self, user_id: str, chat_id: str) -> list[ChatMessage]:
        self._require_chat(user_id, chat_id)
        return self._agent.history(user_id, chat_id)

    def delete_chat(self, user_id: str, chat_id: str) -> None:
        """Borra checkpoint y metadatos manteniendo intactos otros chats."""

        self._require_chat(user_id, chat_id)
        # Primero se borra el estado grande. Si SQLite fallara, el chat seguiría
        # visible y el usuario podría reintentar sin dejar un estado huérfano.
        self._agent.delete_thread(user_id, chat_id)
        self._metadata.delete_chat(user_id, chat_id)

    def list_memories(self, user_id: str) -> list[MemoryRecord]:
        self._require_user(user_id)
        return self._agent.list_memories(user_id)

    def delete_memory(self, user_id: str, memory_key: str) -> None:
        self._require_user(user_id)
        self._agent.delete_memory(user_id, memory_key)

    def _require_user(self, user_id: str) -> User:
        user = self._metadata.get_user(user_id)
        if user is None:
            raise ResourceNotFoundError("El usuario seleccionado no existe.")
        return user

    def _require_chat(self, user_id: str, chat_id: str) -> Chat:
        chat = self._metadata.get_chat(user_id, chat_id)
        if chat is None:
            raise ResourceNotFoundError(
                "La conversación no existe o pertenece a otro usuario."
            )
        return chat
