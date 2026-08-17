# Procesamiento en paralelo

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda , RunnableParallel
import json
import os
# =====================================================
# CONFIGURACIÓN DEL MODELO
# =====================================================
# Creamos una instancia del LLM que utilizaremos en todo el programa.
# temperature=0 hace las respuestas más consistentes.
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# =====================================================
# PREPROCESAMIENTO
# =====================================================
# Esta función recibe el texto original antes de enviarlo al modelo.
# Su objetivo es limpiar espacios innecesarios y limitar longitud.
def preprocess_text(text):
    return text.strip()[:500]
# RunnableLambda permite convertir una función Python normal
# en un componente compatible con las cadenas de LangChain.
preprocessor = RunnableLambda(preprocess_text)

# =====================================================
# GENERACIÓN DE RESUMEN
# =====================================================
# Esta función envía un prompt al modelo para generar un resumen.
def generate_summary(text):

    # Construimos el prompt usando el texto recibido.
    prompt = f"""
    Resume el siguiente texto en una sola oración:

    {text}   """

    # Enviamos el prompt al modelo.
    response = llm.invoke(prompt)
    # response.content contiene el texto generado por el LLM.
    return response.content
# volviendo runeable la función de resumen
summary_brach = RunnableLambda(generate_summary)
# =====================================================
# ANÁLISIS DE SENTIMIENTO
# =====================================================
# Esta función solicita al modelo identificar el sentimiento.
def analyze_sentiment(text):

    # Pedimos explícitamente una respuesta JSON.
    prompt = f"""
    Analiza el sentimiento del siguiente texto.
    Responde únicamente con JSON válido:
    {{
        "sentimiento":"positivo|negativo|neutro",
        "razon":"justificación breve"
    }}

    Texto: {text} """
    
    #===|===| EJECUÓN DE LA LOGICA ==|===|
    try:

        # Llamada al modelo para analizar el sentimiento.
        response = llm.invoke(prompt)

        # Extraemos el texto devuelto.
        content = response.content.strip()

        # Convertimos el JSON de texto a diccionario Python.
        result = json.loads(content)

        # Si el modelo olvidó la clave sentimiento la agregamos.
        if "sentimiento" not in result:
            result["sentimiento"] = "neutro"

        # Si el modelo olvidó la clave razón la agregamos.
        if "razon" not in result:
            result["razon"] = "No especificada"

        # Retornamos el diccionario ya validado.
        return result
    # |==|==|==     EXEPCIONES |==|==|== 
    # Ocurre cuando el modelo devuelve texto que no es JSON.
    except json.JSONDecodeError:
        return {
            "sentimiento": "neutro",
            "razon": "JSON inválido"
        }

    # Captura cualquier otro error inesperado.
    except Exception as e:

        return {
            "sentimiento": "neutro",
            "razon": str(e)
        }
# volviendo runeable la función de sentimiento      
sentiment_brach= RunnableLambda(analyze_sentiment)
# =====================================================
# COMBINACIÓN DE RESULTADOS  - Une el reumsne con el diccionario de sentimientos que tiene (Sentimiento y razon9)
# =====================================================
# Recibe el resumen  y el sentimiento y los une en un solo objeto.
#Simplemente recibe un diccionario que ya fue construido previamente.
def merge_results(data):
    # Retorna el diccionario con todo lo necesario
    return {
        "resumen": data["resumen"],
        "sentimiento": data["sentimiento_data"]["sentimiento"],
        "razon": data["sentimiento_data"]["razon"]
    }
# volviendo runeable la función para unir resultados
merger = RunnableLambda(merge_results)

# no se requiere función orquestadora, creamos un objeto paralelo de langchain donde ejecuta todo en paralelo

parallel_analysis = RunnableParallel({
    # ejecuta funciones runeadas
    "resumen": summary_brach,
    "sentimiento_data" : sentiment_brach
})



#========
#CADENA
#=======
# preprocesa el texto , hace las solicitudes al llm en paralelo , une los resultados 
chain = preprocessor| parallel_analysis | merger
print("chain OK:", chain)  # ← añade esto

# =====================================================
# DATOS DE PRUEBA 
# =====================================================
textos_prueba = [
    "¡Me encanta este producto! Funciona perfectamente y llegó muy rápido.",
    "El servicio al cliente fue terrible, nadie me ayudó con mi problema.",
    "El clima está nublado hoy, probablemente llueva más tarde."
]

# =====================================================
# EJECUCIÓN
# =====================================================
#usandi batch y enviando el listado de textos hace el envio por lotes 
resultado = chain.batch(textos_prueba)
print(resultado)