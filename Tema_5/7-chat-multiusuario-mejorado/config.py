"""Configuración central del chat multiusuario mejorado.

La aplicación importa este módulo desde varias capas. Mantener aquí los
valores cambiantes evita repartir rutas, nombres de modelos y límites por todo
el proyecto. También facilita probar cada pieza con una configuración distinta.
"""

from dataclasses import dataclass
import os
from pathlib import Path


# 1. Las rutas se calculan desde este archivo, no desde la terminal.
#
# Gracias a esto, ``streamlit run app.py`` funciona tanto si se ejecuta dentro
# de esta carpeta como si se indica la ruta desde la raíz del repositorio.
PROJECT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = PROJECT_DIR / "runtime"
METADATA_DB_PATH = RUNTIME_DIR / "metadata.sqlite3"
CHECKPOINT_DB_PATH = RUNTIME_DIR / "checkpoints.sqlite3"
MEMORY_DB_PATH = RUNTIME_DIR / "memories.sqlite3"
KNOWLEDGE_DB_PATH = RUNTIME_DIR / "normative_knowledge.sqlite3"
KNOWLEDGE_FILES_DIR = RUNTIME_DIR / "normative_documents"

# La carpeta se crea al importar la configuración. Los tres archivos SQLite se
# crearán después, cuando cada repositorio abra su conexión.
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_FILES_DIR.mkdir(parents=True, exist_ok=True)


def _read_int(variable_name: str, default: int) -> int:
    """Lee un entero del entorno y falla pronto si su valor no es válido."""

    raw_value = os.getenv(variable_name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as error:
        raise ValueError(
            f"La variable {variable_name} debe contener un número entero."
        ) from error


def _read_float(variable_name: str, default: float) -> float:
    """Lee un decimal del entorno sin ocultar errores de configuración."""

    raw_value = os.getenv(variable_name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as error:
        raise ValueError(
            f"La variable {variable_name} debe contener un número decimal."
        ) from error


# 2. ``Settings`` agrupa la configuración que necesita el núcleo del agente.
#
# Se usa una dataclass inmutable para que ningún componente cambie un valor por
# accidente durante una conversación. Las variables de entorno permiten probar
# otro modelo sin editar el código fuente.
@dataclass(frozen=True)
class Settings:
    """Valores de ejecución del agente, la memoria y la interfaz."""

    chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
    )
    embedding_dimensions: int = _read_int("OPENAI_EMBEDDING_DIMENSIONS", 1536)
    temperature: float = _read_float("CHAT_TEMPERATURE", 0.2)
    max_memory_results: int = _read_int("MAX_MEMORY_RESULTS", 5)
    max_knowledge_results: int = _read_int("MAX_KNOWLEDGE_RESULTS", 6)
    max_pdf_bytes: int = _read_int("MAX_PDF_BYTES", 20 * 1024 * 1024)
    max_legal_chunk_characters: int = _read_int(
        "MAX_LEGAL_CHUNK_CHARACTERS",
        6_000,
    )
    max_input_characters: int = _read_int("MAX_INPUT_CHARACTERS", 8_000)
    # El panel de carga queda deshabilitado hasta que el administrador defina
    # una contraseña. No se incluye un valor inseguro por defecto en el código.
    knowledge_admin_password: str = os.getenv("KNOWLEDGE_ADMIN_PASSWORD", "")
    page_title: str = "Chat multiusuario mejorado"
    page_icon: str = "🤖"


SETTINGS = Settings()

# Identificador visible para distinguir con certeza una instancia actual de una
# pestaña o proceso antiguo durante las pruebas locales.
APP_BUILD = "7.3.0"
