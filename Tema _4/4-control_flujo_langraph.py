# ==============================================================================
# CONTROL DE FLUJO EN LANGGRAPH CON ARISTAS CONDICIONALES (CONDITIONAL EDGES)
# evita usar tantos if  nativos de python
# ==============================================================================

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ------------------------------------------------------------------------------
# PASO 1: DEFINICIÓN DEL ESTADO (STATE)
# El Estado es el esquema de datos (diccionario con tipos) que compartirá y
# actualizará la información a lo largo de todo el flujo del grafo.
# ------------------------------------------------------------------------------
class State(TypedDict):
    numero: int      # Entrada: número entero a evaluar
    resultado: str   # Salida: mensaje generado ("es par" o "es impar")


# ------------------------------------------------------------------------------
# PASO 2: INICIALIZACIÓN DEL GRAFO
# Instanciamos StateGraph indicándole la estructura de datos (State) que manejará.
# ------------------------------------------------------------------------------
graph = StateGraph(State)


# ------------------------------------------------------------------------------
# PASO 3: DEFINICIÓN Y REGISTRO DE LOS NODOS DE TRABAJO
# Los nodos son funciones que reciben el estado actual y devuelven dicts con
# los cambios o actualizaciones que desean aplicar sobre el Estado.
# ------------------------------------------------------------------------------
def caso_par(state: State) -> dict:
    """Nodo ejecutado cuando el número evaluado es par."""
    return {"resultado": "es par"}

def caso_impar(state: State) -> dict:
    """Nodo ejecutado cuando el número evaluado es impar."""
    return {"resultado": "es impar"}

# Registramos los nodos en el grafo asignándoles una etiqueta/nombre clave
graph.add_node("par", caso_par)
graph.add_node("impar", caso_impar)


# ------------------------------------------------------------------------------
# PASO 4: DEFINICIÓN DE LA FUNCIÓN DE ENRUTAMIENTO (ROUTER)
# Evalúa el estado y retorna el NOMBRE del nodo al cual se debe bifurcar el flujo.
# ------------------------------------------------------------------------------
def decidir_rama(state: State) -> str:
    """Función de decisión que retorna la etiqueta del nodo de destino."""
    if state["numero"] % 2 == 0:
        return "par"    # Redirige hacia el nodo registrado como "par"
    else:
        return "impar"  # Redirige hacia el nodo registrado como "impar"


# ------------------------------------------------------------------------------
# PASO 5: CONEXIÓN DE ARISTAS (EDGES / FLUJO DE EJECUCIÓN)
# Configura cómo viaja el control entre nodos, decisiones e inicio/fin.
# ------------------------------------------------------------------------------
# 5.1 Arista condicional: Desde START se ejecuta 'decidir_rama' para saber a qué nodo ir
graph.add_conditional_edges(
    START,
    decidir_rama,
)

# 5.2 Aristas fijas: Al terminar 'par' o 'impar', el flujo va hacia el final (END)
graph.add_edge("par", END)
graph.add_edge("impar", END)


# ------------------------------------------------------------------------------
# PASO 6: COMPILACIÓN DEL GRAFO
# Valida la estructura del grafo y lo convierte en una aplicación ejecutable.
# ------------------------------------------------------------------------------
workflow = graph.compile()


# ------------------------------------------------------------------------------
# PASO 7: INVOCACIÓN Y EJECUCIÓN
# Ejecutamos el flujo enviando los datos iniciales y mostramos el resultado final.
# ------------------------------------------------------------------------------
resultado = workflow.invoke({"numero": 7})
print("Resultado final del estado:", resultado)