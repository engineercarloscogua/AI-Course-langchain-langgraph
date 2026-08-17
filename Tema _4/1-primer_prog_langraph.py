# ==============================================================================
# PRIMER PROGRAMA EN LANGGRAPH (FLUJO SECUENCIAL BÁSICO)
# ==============================================================================
# Este archivo muestra el flujo de trabajo más básico en LangGraph:
# 1. Definir un estado con TypedDict.
# 2. Crear un grafo lineal pasando datos entre nodos en secuencia.
# 3. Compilar e invocar el grafo.
# ==============================================================================

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ------------------------------------------------------------------------------
# PASO 1: DEFINICIÓN DEL ESTADO (STATE)
# El Estado es un esquema basado en TypedDict que define las claves (atributos)
# y tipos de datos compartidos entre los nodos del grafo.
# ------------------------------------------------------------------------------
class State(TypedDict):
    texto_original: str  # Entrada: texto recibido inicialmente
    texto_mayus: str     # Salida intermedia: texto transformado a mayúsculas
    longitug: int        # Salida final: cantidad total de caracteres


# ------------------------------------------------------------------------------
# PASO 2: INICIALIZACIÓN DEL GRAFO
# Instanciamos StateGraph pasándole el esquema State que gobernará el flujo.
# ------------------------------------------------------------------------------
graph = StateGraph(State)


# ------------------------------------------------------------------------------
# PASO 3: DEFINICIÓN DE LAS FUNCIONES DE LOS NODOS DE TRABAJO
# Cada nodo es una función pura que toma el estado actual y devuelve un diccionario
# con las claves que desea actualizar dentro del Estado.
# ------------------------------------------------------------------------------
def poner_mayusculas(state: State) -> dict:
    """Nodo 1: Toma 'texto_original' y actualiza 'texto_mayus' a mayúsculas."""
    texto = state['texto_original']
    return {"texto_mayus": texto.upper()}


def contar_caracteres(state: State) -> dict:
    """Nodo 2: Toma 'texto_mayus' y cuenta su longitud enviándola a 'longitug'."""
    texto = state["texto_mayus"]
    return {"longitug": len(texto)}


# ------------------------------------------------------------------------------
# PASO 4: REGISTRO DE LOS NODOS EN EL GRAFO
# Asignamos un identificador/etiqueta única a cada función dentro del grafo.
# ------------------------------------------------------------------------------
graph.add_node("Mayus", poner_mayusculas)
graph.add_node("Contar", contar_caracteres)


# ------------------------------------------------------------------------------
# PASO 5: CONEXIÓN DE ARISTAS (EDGES) - FLUJO SECUENCIAL
# Conectamos el punto de inicio (START) -> Nodo Mayus -> Nodo Contar -> Fin (END).
# ------------------------------------------------------------------------------
graph.add_edge(START, "Mayus")      # Conecta el inicio al primer nodo
graph.add_edge("Mayus", "Contar")   # Flujo desde 'Mayus' hacia 'Contar'
graph.add_edge("Contar", END)       # Conecta el último nodo al final


# ------------------------------------------------------------------------------
# PASO 6: COMPILACIÓN DEL GRAFO
# Valida las conexiones y convierte el esquema en un objeto Runnable listo para ejecutar.
# ------------------------------------------------------------------------------
compiled_graph = graph.compile()


# ------------------------------------------------------------------------------
# PASO 7: INVOCACIÓN Y EJECUCIÓN
# Ejecutamos el flujo pasando el diccionario con la clave requerida 'texto_original'.
# ------------------------------------------------------------------------------
estado_inicial = {"texto_original": "Hola mundo"}
resultado = compiled_graph.invoke(estado_inicial)

print("Resultado final del estado:", resultado)