# El decorador @tool es la forma recomendada de convertir una función de Python
# en una herramienta que pueda utilizar un agente de LangChain.
from langchain.tools import tool

# StructuredTool está en langchain_core. Esta clase permite convertir una
# función con uno o varios parámetros en una herramienta con esquema validado.
from langchain_core.tools import StructuredTool


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


# Esta es una función normal de Python; todavía no es una herramienta.
# StructuredTool.from_function se encargará de convertirla más adelante.
def herramienta_personalizada2(query: str) -> str:
    """Realiza una consulta personalizada en la base de usuarios."""
    return f"respuesta de la consulta {query}"


# `from_function` inspecciona automáticamente:
# - el nombre de la función para nombrar la herramienta;
# - el docstring para obtener su descripción;
# - las anotaciones de tipo para construir y validar el esquema de entrada.
mi_tool = StructuredTool.from_function(func=herramienta_personalizada2)

# StructuredTool espera sus argumentos como un diccionario. La clave `query`
# debe coincidir con el nombre del parámetro de `herramienta_personalizada2`.
resultado = mi_tool.invoke({"query": "Consulta personalizada"})

# Mostramos el resultado y los metadatos generados por LangChain.
print(resultado)
print(f"nombre de la herramienta: {mi_tool.name}")
print(f"descripción de la herramienta: {mi_tool.description}")
print(f"esquema de argumentos: {mi_tool.args}")
