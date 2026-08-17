# ==============================================================================
# CONFIGURACIÓN GLOBAL DEL SISTEMA - HELPDESK SYSTEM (2026)
# ==============================================================================
# Este archivo centraliza todas las constantes y rutas de configuración.
# Usamos Pathlib para asegurar compatibilidad multiplataforma (Windows, Linux, Mac)
# sin hardcodear rutas absolutas de un usuario específico.
# ==============================================================================

from pathlib import Path

# PASO 1: Determinar el directorio base del proyecto de forma dinámica
BASE_DIR = Path(__file__).parent.resolve()

# PASO 2: Ruta donde se creará y persistirá la base de datos vectorial ChromaDB
CHROMADB_PATH = str(BASE_DIR / "chroma_db")

# PASO 3: Ruta donde residen los documentos Markdown (.md) de la base de conocimiento
DOCS_PATH = str(BASE_DIR / "docs")

# PASO 4: Modelo de embeddings de OpenAI (text-embedding-3-large para máxima calidad vectorial)
EMBEDDINGS_MODEL = "text-embedding-3-large"

# PASO 5: Modelo de lenguaje grande (LLM) para razonamiento, clasificación y respuestas
LLM_MODEL = "gpt-4o-mini"