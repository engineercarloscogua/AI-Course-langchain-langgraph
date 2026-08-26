"""Ejemplo básico de tool calling con LangChain y un modelo de OpenAI.

El modelo no consulta la base de datos directamente. Primero decide si necesita
usar la herramienta y genera los argumentos para llamarla. Después, la cadena
de LangChain ejecuta la función de Python con esos argumentos.

Antes de ejecutar el archivo debe existir la variable de entorno
OPENAI_API_KEY, que es la credencial utilizada por ``ChatOpenAI``.
"""

from operator import attrgetter

from langchain.tools import tool
from langchain_openai import ChatOpenAI


# ChatOpenAI crea el objeto que se comunica con el modelo.
# Una temperatura baja hace que las respuestas sean menos aleatorias, aunque
# no garantiza que dos ejecuciones produzcan exactamente el mismo resultado.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)


# @tool transforma una función normal de Python en una herramienta de
# LangChain. El modelo recibirá su nombre, su descripción y el esquema de sus
# argumentos, pero no podrá ver ni modificar el cuerpo de la función.
#
# - "user_db_tool" es el nombre que verá el modelo.
# - La anotación `query: str` genera el esquema del argumento de entrada.
# - La docstring explica al modelo cuándo y para qué debe usar la herramienta.
# - `return_direct=True` se usa cuando la herramienta forma parte de un agente:
#   indica que su resultado puede devolverse sin otro paso del agente. En esta
#   cadena manual no cambia el flujo, pero se conserva para mostrar la opción.
@tool("user_db_tool", return_direct=True)
def herramienta_personalizada(query: str) -> str:
    """Consulta la base de usuarios de la empresa y devuelve el resultado."""
    # En una aplicación real, aquí se validaría `query` y se consultaría la base
    # de datos. Para mantener el ejemplo sencillo, se devuelve un texto simulado.
    return f"respuesta de la consulta {query}"


# `bind_tools` informa al modelo de qué herramientas dispone y qué argumentos
# acepta cada una. Importante: enlazar la herramienta todavía no la ejecuta.
llm_with_tools = llm.bind_tools([herramienta_personalizada])


# El operador `|` construye una cadena LCEL con tres pasos:
#
# 1. `llm_with_tools` recibe el mensaje y devuelve un `AIMessage`.
# 2. `attrgetter("tool_calls")` extrae la lista de llamadas a herramientas que
#    el modelo incluyó en ese mensaje. Cada llamada contiene nombre, argumentos
#    e identificador.
# 3. `.map()` ejecuta `herramienta_personalizada` una vez por cada llamada de la
#    lista. El resultado final es una lista de objetos `ToolMessage`.
#
# El modelo puede decidir no solicitar ninguna herramienta. En ese caso, esta
# cadena devuelve una lista vacía y no habría un elemento `response[0]`.
chain = llm_with_tools | attrgetter("tool_calls") | herramienta_personalizada.map()


# `invoke` inicia de forma síncrona todo el flujo descrito arriba.
response = chain.invoke(
    "Genera un resumen de la información que hay en la base de datos "
    "del usuario EDx128596"
)


# `response[0]` es el primer `ToolMessage`; `.content` contiene el texto que
# devolvió la función `herramienta_personalizada`. Aquí no se vuelve a llamar al
# modelo después de ejecutar la herramienta, por lo que se imprime el resultado
# simulado de la consulta, no un resumen redactado por el LLM.
print(response[0].content)
