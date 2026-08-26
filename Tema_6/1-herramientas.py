# Tool permite convertir una función normal de Python en una herramienta de
# LangChain. Posteriormente, un agente puede elegir y ejecutar esta herramienta.
from langchain_core.tools import Tool


# Esta función contiene la lógica real de nuestra herramienta. Recibe dos
# números separados por una coma, los convierte a float y devuelve su suma.
def sumar_numeros(entrada: str) -> str:
    """Suma dos números recibidos con el formato 'numero1, numero2'."""
    numero_1, numero_2 = entrada.split(",")
    resultado = float(numero_1) + float(numero_2)
    return str(resultado)


# Envolvemos la función `sumar_numeros` en un objeto Tool.
# - name: nombre único que identifica la herramienta ante el modelo.
# - func: función de Python que LangChain ejecutará.
# - description: explica qué hace y cuál es el formato esperado de entrada.
calculadora = Tool(
    name="sumar_numeros",
    func=sumar_numeros,
    description="Suma dos números. La entrada debe tener el formato 'numero1, numero2'.",
)

# `invoke` es la interfaz moderna y común de los componentes de LangChain.
# Internamente llama a `sumar_numeros("2, 2")` y devuelve "4.0".
output = calculadora.invoke("2, 2")

# Mostramos el resultado de la herramienta en la terminal.
print(output)
