"""Funciones pequeñas de presentación y validación para ``app.py``.

Mantener estas operaciones fuera de la interfaz evita repetirlas y permite
probarlas sin iniciar Streamlit, LangGraph ni los modelos de OpenAI.
"""

from datetime import datetime
import re


# 1. Convierte el formato persistente a uno breve para la interfaz.
def format_timestamp(timestamp_str: str | None) -> str:
    """Formatea un timestamp ISO 8601; devuelve el texto original si es inválido."""

    # Los checkpoints antiguos pueden no tener timestamp. La cadena vacía hace
    # que app.py omita la fecha sin mostrar "None" al usuario.
    if not timestamp_str:
        return ""

    try:
        # fromisoformat entiende offsets como +00:00. La Z usada habitualmente
        # para UTC se normaliza a ese formato antes de construir el datetime.
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (AttributeError, TypeError, ValueError):
        # Un dato antiguo o corrupto sigue siendo visible en lugar de detener la UI.
        return str(timestamp_str)


# 2. Limita textos largos conservando una señal visual de que fueron recortados.
def truncate_text(text: str, max_length: int = 100) -> str:
    """Recorta ``text`` a ``max_length`` caracteres y agrega puntos suspensivos."""

    if max_length <= 0:
        return ""
    if max_length < 3:
        # Se necesitan tres posiciones para representar los puntos suspensivos.
        return text[:max_length]
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


# 3. Aplica en la UI una forma sencilla y predecible para los identificadores.
def validate_user_id(user_id: str) -> bool:
    """Acepta IDs de 2 a 30 caracteres alfanuméricos, ``-`` o ``_``."""

    # fullmatch exige que toda la entrada cumpla el patrón. Así se rechazan
    # espacios y separadores de rutas antes de llegar a memory_manager.py.
    pattern = r"[a-zA-Z0-9_-]{2,30}"
    return re.fullmatch(pattern, user_id) is not None


# 4. Traduce las categorías persistidas a indicadores puramente visuales.
def get_memory_category_icon(category: str) -> str:
    """Devuelve el icono de una categoría o uno genérico si no se conoce."""

    icons = {
        "personal": "👤",
        "profesional": "💼",
        "preferencias": "❤️",
        "tareas": "📝",
        "hechos_importantes": "⭐",
    }
    return icons.get(category, "📌")
