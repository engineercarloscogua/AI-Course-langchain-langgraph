"""Extracción estructurada de varios recuerdos después de cada respuesta."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.prompts import MEMORY_EXTRACTION_PROMPT
from domain.models import MemoryBatch


class MemoryExtractor:
    """Convierte un mensaje libre en una lista validada de hechos duraderos."""

    def __init__(self, model: ChatOpenAI):
        # JSON Schema hace que el proveedor entregue la estructura pedida. Luego
        # Pydantic vuelve a validar claves, categorías, longitudes e importancia.
        self._structured_model = model.with_structured_output(
            MemoryBatch,
            method="json_schema",
        )

    def extract(self, user_message: str) -> MemoryBatch:
        """Extrae todos los hechos independientes del último mensaje humano."""

        result = self._structured_model.invoke(
            [
                SystemMessage(content=MEMORY_EXTRACTION_PROMPT),
                HumanMessage(content=user_message),
            ]
        )

        # Normalmente LangChain ya devuelve MemoryBatch. La segunda rama hace el
        # adaptador resistente a modelos/proveedores que entreguen un diccionario.
        if isinstance(result, MemoryBatch):
            return result
        return MemoryBatch.model_validate(result)
