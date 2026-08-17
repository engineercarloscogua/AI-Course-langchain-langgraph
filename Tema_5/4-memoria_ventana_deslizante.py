"""Memoria conversacional con una ventana deslizante en LangGraph.

El checkpointer conserva el historial completo de cada ``thread_id``, pero el
modelo recibe solamente los mensajes más recientes que caben en la ventana.
Esta técnica reduce el contexto enviado al modelo sin borrar el historial.

En este ejemplo la ventana se mide por CANTIDAD DE MENSAJES, no por tokens.
"""


# PASO 1: IMPORTAR LAS HERRAMIENTAS NECESARIAS
# ------------------------------------------------------------
# HumanMessage representa una entrada del usuario.
# SystemMessage contiene las instrucciones generales del asistente.
# trim_messages selecciona qué parte del historial verá el modelo.
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages

# ChatOpenAI conecta el programa con un modelo de OpenAI.
from langchain_openai import ChatOpenAI

# InMemorySaver guarda temporalmente el estado de cada conversación en RAM.
from langgraph.checkpoint.memory import InMemorySaver

# MessagesState contiene la lista acumulable state["messages"].
# StateGraph construye el flujo y START representa su punto de entrada.
from langgraph.graph import START, MessagesState, StateGraph


# PASO 2: CONFIGURAR EL ASISTENTE Y EL TAMAÑO DE LA VENTANA
# ------------------------------------------------------------
SYSTEM_PROMPT = (
    "Eres un asistente amigable. Usa la conversación reciente disponible "
    "para responder con contexto."
)

# Conservaremos dos turnos anteriores completos. Cada turno tiene un mensaje
# HumanMessage y un AIMessage. Además se incluye la nueva pregunta del usuario.
PREVIOUS_TURNS_IN_WINDOW = 2

# Antes de llamar al modelo, la secuencia máxima será:
# Human, AI, Human, AI, Human(nuevo) = 5 mensajes conversacionales.
MAX_CONVERSATION_MESSAGES = PREVIOUS_TURNS_IN_WINDOW * 2 + 1


# PASO 3: CREAR EL MODELO DE LENGUAJE
# ------------------------------------------------------------
# El modelo no guarda memoria por sí mismo. LangGraph recupera el historial del
# thread_id, prepara la ventana y se la vuelve a enviar en cada invocación.
# temperature=0 reduce la aleatoriedad de las respuestas.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# PASO 4: CONFIGURAR EL RECORTADOR DE MENSAJES
# ------------------------------------------------------------
# trim_messages usa el nombre genérico max_tokens, pero al pasar len como
# token_counter hacemos que cuente MENSAJES completos en lugar de tokens.
# Sumamos 1 porque el límite también cuenta el SystemMessage.
trimmer = trim_messages(
    strategy="last",                           # Conservar lo más reciente.
    max_tokens=MAX_CONVERSATION_MESSAGES + 1,   # Incluir también el sistema.
    token_counter=len,                          # Contar mensajes, no tokens.
    start_on="human",                          # Comenzar con una pregunta.
    include_system=True,                        # Conservar las instrucciones.
    allow_partial=False,                        # No cortar mensajes por la mitad.
)


# PASO 5: DEFINIR EL NODO QUE LLAMA AL MODELO
# ------------------------------------------------------------
# Un nodo recibe el estado actual y devuelve únicamente los cambios que deben
# agregarse a ese estado. MessagesState ya incluye el reductor add_messages.
def chatbot_node(state: MessagesState) -> dict:
    """Responde usando una ventana con los mensajes más recientes."""

    # 5.1: Construir el historial de entrada completo.
    # El SystemMessage se coloca antes de recortar para que include_system=True
    # pueda detectarlo y conservarlo correctamente.
    full_context = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

    # 5.2: Aplicar la ventana deslizante.
    # Al crecer la conversación, salen por la izquierda los mensajes antiguos
    # y permanecen los más recientes. El estado original NO se modifica aquí.
    context_window = trimmer.invoke(full_context)

    # 5.3: Invocar el modelo únicamente con la ventana resultante.
    response = llm.invoke(context_window)

    # 5.4: Agregar la nueva respuesta al estado completo.
    # Gracias a MessagesState, esta lista se combina con los mensajes guardados
    # en vez de reemplazarlos.
    return {"messages": [response]}


# PASO 6: CONSTRUIR EL GRAFO DE EJECUCIÓN
# ------------------------------------------------------------
# 6.1: MessagesState será la estructura oficial del estado del grafo.
workflow = StateGraph(MessagesState)

# 6.2: Registrar el nodo con el nombre "chatbot".
workflow.add_node("chatbot", chatbot_node)

# 6.3: Ejecutar "chatbot" inmediatamente después de START.
# Como el nodo no tiene otra salida, el grafo termina después de responder.
workflow.add_edge(START, "chatbot")


# PASO 7: AGREGAR MEMORIA Y COMPILAR EL GRAFO
# ------------------------------------------------------------
# 7.1: InMemorySaver mantiene un historial independiente para cada thread_id.
# Su contenido desaparece cuando finaliza el proceso de Python.
memory = InMemorySaver()

# 7.2: Compilar convierte la definición en una aplicación ejecutable y conecta
# el checkpointer con el estado del grafo.
app = workflow.compile(checkpointer=memory)


# PASO 8: CREAR LA FUNCIÓN DE CONVERSACIÓN
# ------------------------------------------------------------
def chat(message: str, thread_id: str = "sesion_terminal") -> str:
    """Envía un mensaje a una conversación y devuelve la última respuesta."""

    # 8.1: Identificar la conversación.
    # - Reutilizar el thread_id continúa el mismo historial.
    # - Usar otro thread_id inicia una conversación independiente.
    config = {"configurable": {"thread_id": thread_id}}

    # 8.2: Enviar solamente el mensaje nuevo.
    # Antes de ejecutar el nodo, el checkpointer recupera los mensajes anteriores
    # y MessagesState agrega este HumanMessage al historial recuperado.
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # 8.3: El último mensaje del estado es la respuesta recién generada.
    return result["messages"][-1].content


# PASO 9: EJECUTAR EL CHAT EN LA TERMINAL
# ------------------------------------------------------------
# Este bloque no se ejecuta si el archivo se importa desde otro módulo.
if __name__ == "__main__":
    print("Chat con ventana deslizante (escribe 'salir' para terminar)\n")
    print(
        "El modelo verá la pregunta actual y hasta "
        f"{PREVIOUS_TURNS_IN_WINDOW} turnos anteriores.\n"
    )

    # Usamos la misma sesión durante todo el bucle para continuar la conversación.
    session_id = "sesion_terminal"

    while True:
        try:
            # 9.1: Leer el mensaje y quitar espacios al inicio y al final.
            user_input = input("Escribe tu solicitud: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Permitir también la salida con Ctrl+Z/Ctrl+D o Ctrl+C.
            print("\n¡Hasta luego!")
            break

        # 9.2: Ignorar entradas vacías.
        if not user_input:
            continue

        # 9.3: Terminar al recibir uno de los comandos de salida.
        if user_input.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        # 9.4: Procesar el turno y mostrar la respuesta del asistente.
        respuesta = chat(user_input, session_id)
        print("Asistente:", respuesta)
