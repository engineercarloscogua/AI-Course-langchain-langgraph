from langchain_core.prompts import ChatPromptTemplate
# permite definir lista de mensajes en laplantilla, de acuerdo a distintos roles
from langchain_openai import ChatOpenAI

# temperature=0.5: Controla la "creatividad" (0=predecible, 1=creativo)
chat_model = ChatOpenAI(
    model="gpt-4o-mini",     # El modelo a usar
    temperature=0.5          # Temperatura (balance entre certeza y creatividad)
)

#Roles
chat_prompt  = ChatPromptTemplate.from_messages([
    # Tipos de mensajes
    ("system", "Eres un traductor del español al ingles y eres muy preciso"),
    ("human",  "{texto}")
])

"""
#probando los roles antes de envial al LLM
mensajes = chat_prompt.format_messages(texto = "Hola, me gusta el cafe")

for m in mensajes: 
    print(f"{type(m)}: {m.content}")

"""
# enviando al LLm
mensajes = chat_prompt.invoke({"texto": "Hola, adoro salir de fiesta los domingo"}) # define la petición
respuesta = chat_model.invoke(mensajes) # la envia al modelo y da una respuesta
print(respuesta.content) # muestra el contenido de esa respuesta