"""Herramientas pequeñas y controladas que el modelo puede elegir.

Una herramienta amplía las capacidades del LLM, pero también amplía aquello
que puede hacer de forma autónoma. Por eso este ejercicio expone únicamente
operaciones de lectura: recuerdos, conocimiento normativo y hora actual. El
guardado de memoria y la publicación de normas permanecen en casos de uso
deterministas de la aplicación.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.tools import ToolRuntime, tool

from domain.models import AgentContext
from domain.ports import NormativeKnowledgeSearchPort
from infrastructure.memory_repository import safe_memory_search


@tool
def recall_user_memories(
    query: str,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Busca recuerdos confirmados del usuario actual relacionados con `query`."""

    # ``runtime.context.user_id`` proviene de la aplicación, no de argumentos
    # elegidos por el modelo. Esta es la frontera que impide consultar otro
    # usuario cambiando un supuesto parámetro user_id.
    if runtime.store is None:
        return "El almacén de recuerdos no está disponible."

    items = safe_memory_search(
        runtime.store,
        runtime.context.user_id,
        query,
        limit=8,
    )
    if not items:
        return "No hay recuerdos confirmados relacionados con esa consulta."

    return "\n".join(
        f"- {item.value.get('content', '')}" for item in items
    )


@tool
def current_datetime_bogota() -> str:
    """Devuelve la fecha y hora actuales en la zona horaria de Bogotá."""

    current = datetime.now(ZoneInfo("America/Bogota"))
    return current.isoformat(timespec="seconds")


def build_agent_tools(
    knowledge: NormativeKnowledgeSearchPort,
) -> list:
    """Inyecta el recuperador global sin convertirlo en una variable oculta."""

    @tool("search_traffic_regulations")
    def search_traffic_regulations(query: str) -> str:
        """Busca evidencia vigente en la base compartida de normas de tránsito."""

        try:
            results = knowledge.search(query, limit=8)
        except Exception as error:
            return (
                "La base normativa no está disponible en este momento. No "
                "respondas la consulta jurídica como si hubieras encontrado "
                f"evidencia. Detalle técnico: {type(error).__name__}."
            )
        if not results:
            return (
                "No se encontró evidencia vigente relacionada en la base "
                "normativa. No completes la respuesta jurídica de memoria."
            )
        return "\n\n---\n\n".join(
            f"EVIDENCIA {index}\n{result.prompt_block()}"
            for index, result in enumerate(results, start=1)
        )

    return [
        recall_user_memories,
        search_traffic_regulations,
        current_datetime_bogota,
    ]
