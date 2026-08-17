
''' ESTE ES UN EJEMPLO SENSILLO E INDEPENDIENTE DE COMO USAR LLM DE GEMINI '''
# IMPORTAR CLASE PARA HACER PETICIÓN A LLM DE google
from langchain_google_genai import ChatGoogleGenerativeAI

# Iniciar el modelo LLM
llm = ChatGoogleGenerativeAI( model="gemini-2.5-flash", temperature=0.7)

pregunta = "Quien es el presidente de colombia en 2026?"
print(f"Pregunta: {pregunta}")

# Realizamos la invocación
try:
    # invocando al llm enviadole la pregunta
    respuesta = llm.invoke(pregunta)
    print("-" * 30)
    print(f"Respuesta del modelo: {respuesta.content}")
    print("-" * 30)
except Exception as e:
    print(f"Ocurrió un error al consultar la API: {e}")