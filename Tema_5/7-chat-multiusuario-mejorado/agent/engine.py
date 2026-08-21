"""Adaptador que ensambla y ejecuta el agente moderno.

Patrón utilizado: un *agent harness* dentro de un flujo determinista.

1. La aplicación recupera contexto de largo plazo.
2. ``create_agent`` deja al modelo decidir si necesita una herramienta.
3. LangGraph conserva el hilo completo mediante checkpoints.
4. Tras una respuesta exitosa, un extractor estructurado guarda varios hechos.

La autonomía queda limitada al paso 2. Crear usuarios, aislar datos y escribir
memoria son reglas del programa, no decisiones libres del modelo.
"""

import sqlite3
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    ConflictError,
    InternalServerError,
    RateLimitError,
)

from agent.memory_extractor import MemoryExtractor
from agent.prompts import personalized_system_prompt
from agent.tools import build_agent_tools
from config import Settings
from domain.models import (
    AgentContext,
    AgentReply,
    ChatMessage,
    ExternalServiceError,
    MemoryRecord,
    utc_now_iso,
)
from domain.ports import NormativeKnowledgeSearchPort
from infrastructure.memory_repository import LongTermMemoryRepository


def is_retryable_model_error(error: Exception) -> bool:
    """Indica si repetir la llamada puede resolver el fallo.

    No se reintentan errores de autenticación ni solicitudes inválidas: repetir
    exactamente la misma petición solo aumenta la espera y el consumo. Sí se
    reintentan red, timeout, límite temporal, conflicto y errores 5xx.
    """

    if isinstance(
        error,
        (
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
            ConflictError,
            InternalServerError,
        ),
    ):
        return True
    return isinstance(error, APIStatusError) and error.status_code == 408


def build_model_retry_middleware() -> ModelRetryMiddleware:
    """Crea la política de reintentos sin convertir errores en respuestas."""

    return ModelRetryMiddleware(
        max_retries=2,
        retry_on=is_retryable_model_error,
        # ``continue`` fabrica un AIMessage con "Model call failed...". Ese era
        # el defecto visible en la interfaz. ``error`` conserva la excepción para
        # que la aplicación la maneje como fallo y nunca como respuesta del bot.
        on_failure="error",
    )


def is_legacy_retry_message(content: str) -> bool:
    """Reconoce respuestas técnicas creadas por la configuración defectuosa."""

    return content.strip().startswith("Model call failed after ")


class LangChainAgentGateway:
    """Implementa el puerto del agente con LangChain, LangGraph y OpenAI."""

    def __init__(
        self,
        settings: Settings,
        checkpoint_path: Path | str,
        memory_path: Path | str,
        knowledge: NormativeKnowledgeSearchPort,
    ):
        self._settings = settings
        self._knowledge = knowledge

        # 1. Memoria corta: una sola base puede servir a todos los chats porque
        # el thread_id incluye usuario + chat. SQLiteSaver serializa checkpoints
        # de LangGraph, incluidos mensajes y llamadas de herramientas.
        self._checkpoint_connection = sqlite3.connect(
            str(checkpoint_path),
            check_same_thread=False,
        )
        self._checkpoint_connection.execute("PRAGMA journal_mode=WAL")
        self._checkpointer = SqliteSaver(self._checkpoint_connection)
        self._checkpointer.setup()

        # 2. Memoria larga: SqliteStore usa un índice vectorial. El modelo de
        # embeddings solo convierte texto en vectores; no genera respuestas.
        self._memory_connection = sqlite3.connect(
            str(memory_path),
            check_same_thread=False,
            isolation_level=None,
        )
        self._memory_connection.execute("PRAGMA journal_mode=WAL")
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )
        self._store = SqliteStore(
            self._memory_connection,
            index={
                "embed": embeddings,
                "dims": settings.embedding_dimensions,
                "fields": ["content"],
            },
        )
        self._store.setup()
        self._memories = LongTermMemoryRepository(
            self._store,
            max_results=settings.max_memory_results,
        )

        # 3. Modelo conversacional: Responses API es la interfaz recomendada
        # para razonamiento, herramientas y conversaciones multi-turno actuales.
        chat_model = ChatOpenAI(
            model=settings.chat_model,
            temperature=settings.temperature,
            use_responses_api=True,
            max_retries=0,
            timeout=60,
        )

        # El extractor usa Chat Completions con JSON Schema. En las versiones
        # verificadas, esa combinación evita una advertencia de serialización que
        # aparece al parsear Pydantic directamente desde Responses API. El agente
        # conversacional sí permanece sobre Responses API.
        extraction_model = ChatOpenAI(
            model=settings.chat_model,
            temperature=0,
            use_responses_api=False,
            max_retries=2,
            timeout=60,
        )
        self._extractor = MemoryExtractor(extraction_model)

        # 4. ``create_agent`` construye el bucle modelo -> herramientas -> modelo.
        # El middleware personaliza el prompt y el de reintentos hace resiliente
        # la llamada sin mezclar esa política con los casos de uso.
        self._agent = create_agent(
            model=chat_model,
            tools=build_agent_tools(knowledge),
            middleware=[
                personalized_system_prompt,
                build_model_retry_middleware(),
            ],
            context_schema=AgentContext,
            checkpointer=self._checkpointer,
            store=self._store,
            name="multiuser_personal_assistant",
        )

    @staticmethod
    def _thread_id(user_id: str, chat_id: str) -> str:
        """Crea un identificador global que mantiene aislados usuario y chat."""

        return f"{user_id}:{chat_id}"

    @classmethod
    def _thread_config(cls, user_id: str, chat_id: str) -> dict:
        """Construye la configuración esperada por el checkpointer."""

        return {
            "configurable": {
                "thread_id": cls._thread_id(user_id, chat_id),
            }
        }

    @staticmethod
    def _text(message: AIMessage | HumanMessage) -> str:
        """Normaliza texto simple y bloques de contenido de Responses API."""

        text = message.text
        return text if isinstance(text, str) else str(text)

    def _clean_legacy_retry_messages(self, config: dict):
        """Elimina del checkpoint errores que antes se guardaron como respuestas.

        ``RemoveMessage`` usa el reducer oficial de mensajes de LangGraph. Solo
        se eliminan AIMessage con el prefijo exacto generado por
        ModelRetryMiddleware; los mensajes humanos permanecen intactos.
        """

        state = self._agent.get_state(config)
        removals = [
            RemoveMessage(id=item.id)
            for item in state.values.get("messages", [])
            if isinstance(item, AIMessage)
            and item.id
            and is_legacy_retry_message(self._text(item))
        ]
        if removals:
            self._agent.update_state(config, {"messages": removals})
            return self._agent.get_state(config)
        return state

    def reply(self, user_id: str, chat_id: str, message: str) -> AgentReply:
        """Ejecuta un turno y actualiza memoria sin sacrificar la respuesta."""

        config = self._thread_config(user_id, chat_id)
        self._clean_legacy_retry_messages(config)

        # 5. El contexto relevante se calcula una sola vez antes del bucle. Si
        # los embeddings fallan, el repositorio aplica su búsqueda local.
        memories = self._memories.search(user_id, message)
        try:
            normative_results = self._knowledge.search(message)
        except Exception:
            # El agente sigue disponible para consultas generales. Si la
            # pregunta es jurídica, el prompt le exigirá usar la herramienta o
            # reconocer que no dispone de evidencia suficiente.
            normative_results = []
        context = AgentContext(
            user_id=user_id,
            relevant_memories=tuple(memory.content for memory in memories),
            relevant_norms=tuple(
                result.prompt_block() for result in normative_results
            ),
        )
        human_message = HumanMessage(
            content=message,
            additional_kwargs={"created_at": utc_now_iso()},
        )

        try:
            result = self._agent.invoke(
                {"messages": [human_message]},
                config=config,
                context=context,
            )
        except APIConnectionError as error:
            raise ExternalServiceError(
                "No fue posible conectar con OpenAI. La conversación no se "
                "registró como completada; verifica la conexión de red del servidor."
            ) from error
        except AuthenticationError as error:
            raise ExternalServiceError(
                "OpenAI rechazó la clave de API. Verifica OPENAI_API_KEY."
            ) from error
        except RateLimitError as error:
            raise ExternalServiceError(
                "OpenAI alcanzó temporalmente el límite de solicitudes o saldo. "
                "Espera un momento y vuelve a intentarlo."
            ) from error
        except Exception as error:
            raise ExternalServiceError(
                "No fue posible obtener una respuesta del modelo. "
                f"Detalle: {type(error).__name__}: {error}"
            ) from error

        final_message = next(
            (
                item
                for item in reversed(result.get("messages", []))
                if isinstance(item, AIMessage)
                and not item.tool_calls
                and self._text(item).strip()
            ),
            None,
        )
        if final_message is None:
            raise ExternalServiceError("El agente terminó sin producir una respuesta.")

        response_text = self._text(final_message).strip()

        # 6. La memoria larga es una mejora posterior a la respuesta. Si falla,
        # el usuario conserva su respuesta y recibe un aviso no fatal.
        try:
            batch = self._extractor.extract(message)
            saved = self._memories.save_many(user_id, batch.facts, source=message)
            return AgentReply(content=response_text, memories_saved=saved)
        except Exception as error:
            return AgentReply(
                content=response_text,
                warning=(
                    "La respuesta se generó, pero no fue posible actualizar "
                    f"la memoria: {type(error).__name__}: {error}"
                ),
            )

    def history(self, user_id: str, chat_id: str) -> list[ChatMessage]:
        """Lee del checkpoint solo mensajes humanos y respuestas finales."""

        state = self._clean_legacy_retry_messages(
            self._thread_config(user_id, chat_id)
        )
        messages: list[ChatMessage] = []
        for item in state.values.get("messages", []):
            if isinstance(item, HumanMessage):
                messages.append(
                    ChatMessage(
                        role="user",
                        content=self._text(item),
                        created_at=item.additional_kwargs.get("created_at"),
                    )
                )
            elif isinstance(item, AIMessage) and not item.tool_calls:
                content = self._text(item).strip()
                if content:
                    messages.append(
                        ChatMessage(
                            role="assistant",
                            content=content,
                            created_at=item.additional_kwargs.get("created_at"),
                        )
                    )
        return messages

    def delete_thread(self, user_id: str, chat_id: str) -> None:
        """Elimina todos los checkpoints de una conversación."""

        self._checkpointer.delete_thread(self._thread_id(user_id, chat_id))

    def list_memories(self, user_id: str) -> list[MemoryRecord]:
        """Expone una vista auditable de la memoria de largo plazo."""

        return self._memories.list_all(user_id)

    def delete_memory(self, user_id: str, memory_key: str) -> None:
        """Permite al usuario corregir su memoria eliminando un hecho."""

        self._memories.delete(user_id, memory_key)

    def close(self) -> None:
        """Libera conexiones cuando el proceso que aloja la app termina."""

        self._checkpoint_connection.close()
        self._memory_connection.close()
