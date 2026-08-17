#ejemplo de forma rudimentaria de un chat en terminal con memoria de conversación
# noe s correcto usar esta forma porque se almacena todo en la lista de memoria y puede crecer indefinidamente, lo que puede causar problemas de rendimiento y consumo de memoria.
# si hay multiple sesiones de chat, la memoria de conversación puede mezclarse y causar confusión en las respuestas del asistente.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

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
# Inicialización de la memoria de conversación / almacena todos los mensajes de la conversación
history = []

print("Chat en terminal (escribe 'salir' para terminar)\n")
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
    respuesta = chain.invoke({"history": history, "input": user_input})
    print("Asistente:", respuesta.content)
    
    #actiualización de la lista del historial de mensajes en cada iteración
    history.extend(
        [   # Agregar el mensaje del usuario y la respuesta del asistente a la memoria de conversación
            HumanMessage(content=user_input),
            # Agregar la respuesta del asistente a la memoria de conversación 
            AIMessage(content=respuesta.content)
        ]
    )