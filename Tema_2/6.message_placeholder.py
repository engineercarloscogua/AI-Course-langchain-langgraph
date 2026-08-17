from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

#plantilla 
chat_prompt = ChatPromptTemplate.from_messages([
    # mensaje del sistema
    ("system", "Eres un asistente útil que mantiene el contexto de la conversación"),
    # enviamos el historial simulado / placeholder - marcador de posición
    MessagesPlaceholder(variable_name = "historial"),
    # el prompt que le enviaremos 
    ("human", "Usuario  {pregunta_actual}")
])

# sumulación de un historial de conversación
historial = [
    HumanMessage(content = "Usuario: Cuál es la capital de francia?"),
    AIMessage(content = "IA: La capital de francia es París"),
    HumanMessage(content = "Usuario: y cuantos habitantes tiene?"),
    AIMessage(content = "IA: París tiene aproximadamente 2.2 millones de habitantes en la ciudad")    
]

# ==|==| # ==|==|# ==|==|# ==|==|# ==|==|
# probando la plantilla
mensajes = chat_prompt.format_messages(
    #  historial simulado
    historial = historial,
    # nuevo prompt
    pregunta_actual = "¿Puedes decirme algo interesante de su arquitectura? "
)

for contenido_menss in mensajes :
    print(contenido_menss.content)
# ==|==|# ==|==|# ==|==|# ==|==|# ==|==|# ==|
# me quede en el video 34 lectura few- shot