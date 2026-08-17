"""Ejemplo paso a paso de memoria conversacional de corto plazo con LangGraph.

La memoria se conserva por ``thread_id`` mientras este proceso de Python siga
abierto. Al cerrar el programa, ``InMemorySaver`` pierde los datos guardados.
"""

# PASO 1: IMPORTAR LAS HERRAMIENTAS NECESARIAS
# ------------------------------------------------------------
# HumanMessage representa un mensaje escrito por el usuario.
# SystemMessage contiene las instrucciones generales para el modelo.
from langchain_core.messages import HumanMessage, SystemMessage

# ChatOpenAI permite comunicarnos con un modelo de OpenAI.
from langchain_openai import ChatOpenAI

# InMemorySaver guarda temporalmente el estado de cada conversación en RAM.
from langgraph.checkpoint.memory import InMemorySaver

# MessagesState define un estado que contiene una lista acumulable de mensajes.
# StateGraph permite construir el flujo y START representa su punto de entrada.
from langgraph.graph import START, MessagesState, StateGraph


# PASO 2: DEFINIR LAS INSTRUCCIONES DEL ASISTENTE
# ------------------------------------------------------------
# Este mensaje se agrega antes del historial cada vez que llamamos al modelo.
# No se guarda dentro de la memoria, por lo que no se duplica entre turnos.
SYSTEM_PROMPT = (
    "Eres un asistente amigable. Usa la conversación previa disponible "
    "para responder con contexto."
)


# PASO 3: CREAR EL MODELO DE LENGUAJE
# ------------------------------------------------------------
# El modelo NO mantiene memoria por sí solo. En cada llamada, LangGraph le
# enviará nuevamente los mensajes acumulados en el estado de la conversación.
# temperature=0 hace las respuestas menos aleatorias y más reproducibles.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# PASO 4: DEFINIR EL NODO QUE PROCESA LA CONVERSACIÓN
# ------------------------------------------------------------
# Un nodo es una función que recibe el estado actual y devuelve una actualización
# para ese estado. Aquí recibe MessagesState, que contiene state["messages"].
def chatbot_node(state: MessagesState) -> dict:
    """Invoca el modelo con el historial guardado en el estado del grafo."""

    # 4.1: Preparar el contexto que verá el modelo.
    # Primero colocamos el mensaje del sistema y después todo el historial.
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

    # 4.2: Enviar al modelo las instrucciones y el historial completo.
    response = llm.invoke(messages)

    # 4.3: Devolver solamente el nuevo mensaje generado.
    # MessagesState utiliza internamente el reductor add_messages. Por eso esta
    # respuesta se AGREGA al historial y no reemplaza los mensajes anteriores.
    return {"messages": [response]}


# PASO 5: CONSTRUIR EL GRAFO DE EJECUCIÓN
# ------------------------------------------------------------
# 5.1: Crear un grafo cuyo estado tiene la estructura de MessagesState.
workflow = StateGraph(MessagesState)

# 5.2: Registrar nuestra función como un nodo llamado "chatbot".
workflow.add_node("chatbot", chatbot_node)

# 5.3: Indicar que, al comenzar el grafo, se debe ejecutar "chatbot".
# Como no agregamos más nodos, el grafo termina después de ejecutar este nodo.
workflow.add_edge(START, "chatbot")


# PASO 6: AGREGAR MEMORIA Y COMPILAR EL GRAFO
# ------------------------------------------------------------
# 6.1: Crear el checkpointer que guardará los estados en la memoria RAM.
# Es adecuado para aprendizaje y pruebas. Al cerrar Python, la memoria se pierde.
memory = InMemorySaver()

# 6.2: Compilar convierte la definición anterior en una aplicación ejecutable.
# Al pasar el checkpointer, LangGraph guardará un estado por cada thread_id.
app = workflow.compile(checkpointer=memory)


# PASO 7: CREAR UNA FUNCIÓN PARA CONVERSAR
# ------------------------------------------------------------
# message es el nuevo texto del usuario.
# thread_id identifica la conversación a la que pertenece ese mensaje.
def chat(message: str, thread_id: str = "sesion_terminal") -> str:
    """Envía un mensaje dentro de una conversación identificada por thread_id."""

    # 7.1: Construir la configuración de la conversación.
    # La clave debe llamarse literalmente "thread_id".
    # - Mismo thread_id: LangGraph recupera y continúa el historial existente.
    # - Distinto thread_id: LangGraph comienza una conversación independiente.
    config = {"configurable": {"thread_id": thread_id}}

    # 7.2: Ejecutar el grafo.
    # Solo enviamos el mensaje NUEVO. El checkpointer recupera automáticamente
    # los anteriores y MessagesState agrega este HumanMessage al historial.
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # 7.3: El resultado contiene todo el estado actualizado. El último elemento
    # de "messages" es la respuesta que acaba de generar el asistente.
    return result["messages"][-1].content


# PASO 8: CREAR LA INTERFAZ DE CHAT EN LA TERMINAL
# ------------------------------------------------------------
# Este bloque solo se ejecuta cuando abrimos directamente este archivo.
# No se ejecuta cuando el archivo se importa desde otro módulo.
if __name__ == "__main__":
    print("Chat en terminal (escribe 'salir' para terminar)\n")

    # Todos los mensajes escritos durante esta ejecución usan la misma sesión.
    # Por eso el asistente puede recordar lo dicho en turnos anteriores.
    session_id = "sesion_terminal"

    # Repetir hasta que el usuario escriba un comando de salida.
    while True:
        try:
            # 8.1: Leer el nuevo mensaje y quitar espacios en los extremos.
            user_input = input("Escribe tu solicitud: ").strip()
        except (EOFError, KeyboardInterrupt):
            # También permitimos terminar con Ctrl+Z/Ctrl+D o Ctrl+C.
            print("\n¡Hasta luego!")
            break

        # 8.2: Ignorar entradas vacías.
        if not user_input:
            continue

        # 8.3: Finalizar si se recibe uno de estos comandos.
        if user_input.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        # 8.4: Enviar el mensaje usando siempre el mismo thread_id y mostrar
        # solamente el contenido de la última respuesta del asistente.
        respuesta = chat(user_input, session_id)
        print("Asistente:", respuesta)
