# resumen del archivo, aplicación sencilla de mameoria
''' Este archivo implementa un chat en terminal con memoria de 
conversación utilizando LangChain y el modelo de lenguaje GPT-4o-mini.
El chat permite al usuario interactuar con un asistente virtual que
recuerda el contexto de la conversación a través de sesiones.
El historial de conversación se almacena en memoria RAM y se asocia a 
una sesión específica, lo que permite mantener el contexto entre diferentes 
interacciones del usuario. El chat se ejecuta en un bucle que solicita al 
usuario que ingrese su solicitud,'''
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
# Configuración del modelo de lenguaje
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# Configuración del prompt de chat
prompt = ChatPromptTemplate.from_messages([
    # Mensaje del sistema que establece el rol del asistente
    ("system", "Eres un asistente útil."),
    # Configuración de la memoria de conversación
    MessagesPlaceholder(variable_name="history"),
    # Mensaje del usuario que contiene la entrada del usuario
    ("human", "{input}")
])
# Configuración de la cadena de chat
chain = prompt | llm

#====================================================
# Configuración de la memoria de conversación
store = {}
# Función para obtener el historial de conversación de una sesión específica
def get_session_historry(session_id):
    if session_id not in store: #si la sesión no existe, se crea una nueva lista vacía para almacenar el historial de conversación
        #almacena en memoria ram historial de mensajes
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
#====================================================
# definir nueva cadena con memoria automatica por sesion
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_historry,
    input_messages_key="input",
    history_messages_key="history"
)

print("Chat en terminal (escribe 'salir' para terminar)\n")
# Obtener el historial de conversación para la sesión actual
session_id = "sesion_terminal"

# Bucle principal del chat
while True:
    try:
        # Solicitar entrada del usuario
        #strip() elimina espacios en blanco al inicio y al final de la cadena
        user_input = input("Escribe tu solicitud: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nHasta luego!")
        break
    # Manejar entrada vacía o comandos de salida
    if not user_input:
        continue
    # Manejar comandos de salida
    if user_input.lower() in {"salir", "exit", "quit"}:
        print("Hasta luego!")
        break
    # Agregar la entrada del usuario a la memoria de conversación
    respuesta = chain_with_memory.invoke(
        {"input": user_input},
        config ={"configurable": {"session_id" : session_id}}
    )
    print("Asistente:", respuesta.content)
    
   