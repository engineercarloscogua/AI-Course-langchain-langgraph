# El decorador @tool es la forma recomendada de convertir una función de Python
# en una herramienta que pueda utilizar un agente de LangChain.
from langchain.tools import tool


# El decorador registra la función como una herramienta de LangChain.
# - "herramienta_acceso_bd_usuarios" es el nombre que verá el agente.
# - return_direct=True indica que, dentro de un agente, el resultado de esta
#   herramienta debe devolverse directamente al usuario y finalizar ese paso.
@tool("herramienta_acceso_bd_usuarios", return_direct=True)
def herramienta_personalizada(query: str) -> str:
    """Consulta la base de usuarios de la empresa."""
    # `query: str` describe el argumento de entrada y `-> str` indica que el
    # resultado de la herramienta será una cadena de texto.

    # En una aplicación real, aquí se validaría la consulta y se accedería a la
    # base de datos. En este ejemplo solo simulamos la respuesta.
    return f"respuesta de la consulta {query}"


# Ejecutamos manualmente la herramienta mediante `invoke`, la interfaz moderna
# y común de LangChain. El diccionario relaciona cada valor con el parámetro
# correspondiente de la función; aquí asigna el texto al parámetro `query`.
output = herramienta_personalizada.invoke({"query": "consulta de prueba"})

# Mostramos el resultado producido por la función.
print(output)

# @tool crea un objeto con metadatos. `name` proviene del decorador y
# `description` proviene del docstring de la función.
print(f"nombre de la herramienta: {herramienta_personalizada.name}")
print(f"descripción de la herramienta: {herramienta_personalizada.description}")
