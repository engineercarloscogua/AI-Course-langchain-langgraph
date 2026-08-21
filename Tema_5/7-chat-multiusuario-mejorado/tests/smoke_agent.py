"""Prueba manual de integración que sí consume la API de OpenAI.

No comienza por ``test_`` para que ``unittest discover`` no gaste saldo. Se
ejecuta explícitamente cuando se desea validar agente, embeddings, memoria,
checkpointer y servicio en conjunto.
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


# Al ejecutar un archivo dentro de ``tests``, Python toma esa subcarpeta como
# primer origen de imports. Agregamos la raíz del ejercicio para encontrar los
# paquetes ``application``, ``agent`` y ``domain``.
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

# La carga debe ocurrir antes de importar el bootstrap que valida la clave.
load_dotenv()

from agent.engine import LangChainAgentGateway  # noqa: E402
from application.chat_service import ChatApplicationService  # noqa: E402
from config import SETTINGS  # noqa: E402
from infrastructure.knowledge_repository import SQLiteKnowledgeRepository  # noqa: E402
from infrastructure.metadata_repository import SQLiteMetadataRepository  # noqa: E402


def _build_test_application(base_path: Path):
    """Crea el sistema completo usando bases temporales y la API real."""

    metadata = SQLiteMetadataRepository(base_path / "metadata.sqlite3")
    knowledge = SQLiteKnowledgeRepository(
        database_path=base_path / "knowledge.sqlite3",
        embeddings=OpenAIEmbeddings(
            model=SETTINGS.embedding_model,
            dimensions=SETTINGS.embedding_dimensions,
        ),
        embedding_dimensions=SETTINGS.embedding_dimensions,
        max_results=SETTINGS.max_knowledge_results,
    )
    agent = LangChainAgentGateway(
        settings=SETTINGS,
        checkpoint_path=base_path / "checkpoints.sqlite3",
        memory_path=base_path / "memories.sqlite3",
        knowledge=knowledge,
    )
    service = ChatApplicationService(
        metadata=metadata,
        agent=agent,
        max_input_characters=SETTINGS.max_input_characters,
    )
    return metadata, knowledge, agent, service


def main() -> None:
    """Prueba respuesta, varios hechos y persistencia después de reiniciar."""

    # TemporaryDirectory impide que esta prueba contamine los usuarios o chats
    # que la persona ya tenga dentro de ``runtime``.
    with TemporaryDirectory() as temporary_directory:
        base_path = Path(temporary_directory)
        metadata, knowledge, agent, service = _build_test_application(base_path)
        user, chat = service.bootstrap()

        reply = service.send_message(
            user.user_id,
            chat.chat_id,
            (
                "Para esta prueba recuerda tres datos: me llamo Ada Prueba, "
                "vivo en Yopal y mi color favorito es violeta."
            ),
        )
        first_memories = service.list_memories(user.user_id)

        assert reply.content.strip(), "El agente devolvió una respuesta vacía."
        assert reply.warning is None, reply.warning
        assert reply.memories_saved >= 3, (
            "Se esperaban al menos tres recuerdos independientes; "
            f"se guardaron {reply.memories_saved}."
        )

        # 1. Cerrar ambas conexiones simula detener por completo Streamlit.
        agent.close()
        knowledge.close()
        metadata.close()

        # 2. Abrir nuevos objetos sobre los mismos archivos simula reiniciarlo.
        metadata, knowledge, agent, service = _build_test_application(base_path)
        history = service.history(user.user_id, chat.chat_id)
        persisted_memories = service.list_memories(user.user_id)

        assert [message.role for message in history] == ["user", "assistant"]
        assert len(persisted_memories) >= 3
        assert {memory.key for memory in first_memories} == {
            memory.key for memory in persisted_memories
        }

        print("SMOKE_OK")
        print(f"history_messages={len(history)}")
        print(f"persisted_memories={len(persisted_memories)}")

        agent.close()
        knowledge.close()
        metadata.close()


if __name__ == "__main__":
    main()
