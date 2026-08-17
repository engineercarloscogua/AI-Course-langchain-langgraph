"""Chat con memoria persistente construido con LangGraph y SQLite.

Funcionamiento general:
1. La persona escribe un mensaje en la terminal.
2. LangGraph busca en SQLite el historial asociado al ``thread_id``.
3. El mensaje nuevo se agrega al historial recuperado.
4. El modelo recibe las instrucciones y la conversación completa.
5. La respuesta se muestra y el estado actualizado se guarda en
   ``historial.db``.

Como los mensajes quedan almacenados en un archivo, la conversación puede
continuar incluso después de cerrar y volver a ejecutar el programa.
"""


# PASO 1: IMPORTAR LAS HERRAMIENTAS NECESARIAS
# ------------------------------------------------------------
# sqlite3 permite usar una base de datos local sin instalar un servidor.
# Path ayuda a construir la ubicación del archivo de manera segura.
import sqlite3
from pathlib import Path

# HumanMessage representa un mensaje escrito por el usuario.
# SystemMessage contiene las instrucciones generales para el modelo.
from langchain_core.messages import HumanMessage, SystemMessage

# ChatOpenAI permite comunicarnos con un modelo de OpenAI.
from langchain_openai import ChatOpenAI

# SqliteSaver conecta la memoria de LangGraph con una base de datos SQLite.
from langgraph.checkpoint.sqlite import SqliteSaver

# MessagesState representa el estado de la aplicación: una lista de mensajes
# que crece durante la conversación. StateGraph construye el flujo de trabajo
# y START representa su punto de inicio.
from langgraph.graph import START, MessagesState, StateGraph

# PASO 2: DEFINIR LAS INSTRUCCIONES DEL ASISTENTE
# ------------------------------------------------------------
# Este mensaje define cómo debe comportarse el asistente. Se agrega antes de
# cada llamada, pero no se guarda en SQLite; así no se duplica entre turnos.
SYSTEM_PROMPT = (
    "Eres un asistente amigable. Usa la conversación previa disponible "
    "para responder con contexto."
)


# PASO 3: CREAR EL MODELO DE LENGUAJE
# ------------------------------------------------------------
# El modelo no recuerda llamadas anteriores por sí solo. La memoria funciona
# porque LangGraph recupera los mensajes y vuelve a enviárselos en cada turno.
# temperature=0 reduce la aleatoriedad y genera respuestas más consistentes.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# PASO 4: DEFINIR EL NODO QUE PROCESA LA CONVERSACIÓN
# ------------------------------------------------------------
# Un nodo es una tarea dentro del flujo. Este nodo recibe el estado actual,
# llama al modelo y devuelve la respuesta que se agregará a la conversación.
# En este punto solo definimos la función; todavía no se ejecuta.
def chatbot_node(state: MessagesState) -> dict:
    """Invoca el modelo con el historial guardado en el estado del grafo."""

    # 4.1: Preparar el contexto que verá el modelo.
    # state["messages"] contiene el historial recuperado de SQLite y el mensaje
    # nuevo. Las instrucciones generales se colocan al principio.
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

    # 4.2: Enviar el contexto al modelo y esperar su respuesta.
    response = llm.invoke(messages)

    # 4.3: Devolver solamente la respuesta nueva.
    # MessagesState sabe combinar mensajes, por lo que agrega esta respuesta al
    # historial existente en lugar de reemplazarlo.
    return {"messages": [response]}


# PASO 5: CONSTRUIR EL GRAFO DE EJECUCIÓN
# ------------------------------------------------------------
# 5.1: Crear el contenedor del flujo y decirle que usará MessagesState.
workflow = StateGraph(MessagesState)

# 5.2: Registrar la función anterior como una tarea llamada "chatbot".
workflow.add_node("chatbot", chatbot_node)

# 5.3: Conectar el inicio del flujo directamente con el nodo "chatbot".
# Como no existen más nodos, el flujo termina al obtener la respuesta.
workflow.add_edge(START, "chatbot")


# PASO 6: CONFIGURAR LA MEMORIA PERSISTENTE EN SQLITE
# ------------------------------------------------------------
# 6.1: Construir la ruta absoluta de la base de datos.
# __file__ representa este archivo de Python. Su carpeta padre es Tema_5, por
# eso historial.db se crea allí aunque ejecutemos el programa desde otro lugar.
DB_PATH = Path(__file__).resolve().parent / "historial.db"

# 6.2: Abrir la conexión. Si historial.db no existe, SQLite lo crea.
# check_same_thread=False permite que LangGraph use la conexión desde sus tareas.
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# 6.3: Crear el guardador de memoria que leerá y escribirá checkpoints.
# Un checkpoint es una fotografía del estado de la conversación en un momento.
memory = SqliteSaver(conn)


# PASO 7: COMPILAR EL GRAFO Y CONECTAR SU MEMORIA
# ------------------------------------------------------------
# Compilar convierte la definición del flujo en una aplicación ejecutable.
# Al recibir memory como checkpointer, la aplicación guarda y recupera un
# historial independiente para cada thread_id.
app = workflow.compile(checkpointer=memory)


# PASO 8: CREAR UNA FUNCIÓN PARA ENVIAR MENSAJES
# ------------------------------------------------------------
# message contiene el texto nuevo de la persona.
# thread_id funciona como el identificador de una conversación concreta.
def chat(message: str, thread_id: str = "sesion_terminal") -> str:
    """Envía un mensaje dentro de una conversación identificada por thread_id."""

    # 8.1: Indicar qué conversación queremos abrir o continuar.
    # La clave debe llamarse literalmente "thread_id".
    # - Mismo thread_id: LangGraph recupera y continúa el historial existente.
    # - Distinto thread_id: LangGraph comienza una conversación independiente.
    config = {"configurable": {"thread_id": thread_id}}

    # 8.2: Convertir el texto en HumanMessage y ejecutar el grafo.
    # Durante app.invoke ocurren automáticamente estas acciones:
    #   a) SqliteSaver recupera el último estado del thread_id.
    #   b) MessagesState agrega el HumanMessage nuevo al historial.
    #   c) LangGraph ejecuta chatbot_node.
    #   d) La respuesta del modelo se agrega al estado.
    #   e) SqliteSaver guarda el estado actualizado en historial.db.
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # 8.3: Extraer solamente el texto de la respuesta más reciente.
    # result contiene el estado completo y su último mensaje pertenece al modelo.
    return result["messages"][-1].content


# PASO 9: EJECUTAR LA INTERFAZ DE CHAT EN LA TERMINAL
# ------------------------------------------------------------
# Esta condición evita abrir el chat si otro archivo importa este módulo.
# El bloque se ejecuta únicamente cuando iniciamos directamente este programa.
if __name__ == "__main__":
    print("Chat en terminal (escribe 'salir' para terminar)\n")

    # 9.1: Elegir el identificador de la conversación.
    # Como el valor siempre es el mismo, cada nueva ejecución vuelve a abrir el
    # historial de "sesion_terminal" guardado anteriormente en SQLite.
    session_id = "sesion_terminal"

    # 9.2: Mantener el programa activo hasta que la persona decida salir.
    while True:
        try:
            # 9.3: Leer un mensaje y eliminar espacios innecesarios de los lados.
            user_input = input("Escribe tu solicitud: ").strip()
        except (EOFError, KeyboardInterrupt):
            # 9.4: Permitir cerrar de forma segura con Ctrl+C o fin de entrada.
            print("\n¡Hasta luego!")
            break

        # 9.5: No llamar al modelo cuando la persona no escribió nada.
        if not user_input:
            continue

        # 9.6: Cerrar el bucle cuando se escribe un comando de salida.
        if user_input.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        # 9.7: Enviar el mensaje, continuar la sesión y mostrar la respuesta.
        respuesta = chat(user_input, session_id)
        print("Asistente:", respuesta)
