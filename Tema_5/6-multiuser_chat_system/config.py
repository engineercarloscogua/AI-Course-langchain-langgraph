"""Configuración compartida del sistema de chat multiusuario.

Este módulo se ejecuta una sola vez la primera vez que Python lo importa.
Centralizar aquí las rutas y los modelos evita repetir valores en los demás
archivos del proyecto.
"""

# ``os`` contiene utilidades portables para trabajar con rutas y directorios.
# Usarlo evita escribir separadores específicos de Windows (\) o Linux (/).
import os


# 1. Calcula las rutas a partir de la ubicación de este archivo.
#
# 1.1. ``__file__`` es la ruta de config.py.
# 1.2. ``abspath`` la convierte en una ruta absoluta.
# 1.3. ``dirname`` elimina "config.py" y conserva únicamente su carpeta.
#
# No usamos el directorio desde el que se lanzó Python porque este puede variar.
# De este modo, los datos siempre quedan junto al ejercicio.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ``join`` agrega una carpeta a BASE_DIR usando el separador correcto del SO.
# DATA_DIR queda preparado para otros datos que añada el tutorial.
# USERS_DIR contendrá una subcarpeta independiente por cada usuario.
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(BASE_DIR, "users")

# 2. Crea los directorios que contendrán los datos persistentes.
#
# ``makedirs`` crea también carpetas padre si fueran necesarias.
# ``exist_ok=True`` significa: "si ya existe, continúa sin lanzar error".
# Estas líneas se ejecutan al importar config.py, antes de crear el chatbot.
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)

# 3. Configura los modelos de OpenAI.
#
# DEFAULT_MODEL se usa para conversar, extraer recuerdos y generar títulos.
# EMBEDDING_MODEL no responde preguntas: convierte texto en listas de números
# (vectores) para que Chroma pueda comparar significados.
# La temperatura controla la variación: 0 es más determinista; valores mayores
# permiten respuestas algo más creativas.
#
# ``langchain_openai`` lee OPENAI_API_KEY de las variables de entorno; la clave
# nunca debe escribirse directamente en estos archivos.
DEFAULT_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_TEMPERATURE = 0.3

# 4. Define límites para evitar enviar información innecesaria al modelo.
#
# MAX_CONTEXT_TOKENS limita solo la copia del historial enviada al LLM. El
# historial completo sigue persistido en SQLite.
# MAX_VECTOR_RESULTS indica cuántos recuerdos semánticamente cercanos se
# recuperan de Chroma en cada turno.
MAX_CONTEXT_TOKENS = 4_000
MAX_VECTOR_RESULTS = 3

# 5. Enumera las categorías que puede producir el extractor de memoria.
# Es una tupla porque este catálogo es configuración y no debería modificarse
# accidentalmente durante la ejecución.
MEMORY_CATEGORIES = (
    "personal",
    "profesional",
    "preferencias",
    "hechos_importantes",
)

# 6. Define valores de presentación para el archivo de interfaz que el tutorial
# añadirá después. Por ahora no afectan al grafo ni realizan ninguna llamada.
PAGE_TITLE = "Chat multiusuario con memoria avanzada"
PAGE_ICON = "💬"
