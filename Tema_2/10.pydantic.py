# Importamos BaseModel y Field desde Pydantic.
# Pydantic permite definir estructuras de datos con validación automática.
from pydantic import BaseModel, Field

# Importamos el modelo de OpenAI que LangChain utilizará.
from langchain_openai import ChatOpenAI


# ==================================================
# 1. DEFINICIÓN DEL MODELO DE SALIDA
# ==================================================
# Esta clase indica exactamente qué estructura debe
# devolver el LLM.
#
# LangChain utilizará esta definición para obligar
# al modelo a responder en formato estructurado.
#
# Es equivalente a definir un esquema JSON.
# ==================================================

class AnalisisTexto(BaseModel):

    # Resumen corto del texto analizado
    resumen: str = Field(
        description="Resumen breve del texto"
    )

    # Clasificación del sentimiento
    sentimiento: str = Field(
        description="Sentimiento: Positivo, Neutro o Negativo"
    )

    # Lista de palabras clave
    palabras_clave: list[str] = Field(
        description="3 a 5 palabras clave principales"
    )


# ==================================================
# 2. CREAR EL MODELO LLM
# ==================================================
# ChatOpenAI es el modelo que realizará el análisis.
#
# temperature:
#   0 = respuestas más determinísticas
#   1 = respuestas más creativas
#
# Para tareas analíticas suele usarse entre 0 y 0.3
# ==================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2
)


# ==================================================
# 3. CONVERTIR EL MODELO A SALIDA ESTRUCTURADA
# ==================================================
# Aquí ocurre la magia.
#
# LangChain toma la clase AnalisisTexto y genera
# automáticamente las instrucciones para que el
# modelo responda en ese formato.
#
# Ya no necesitamos:
#   - PydanticOutputParser
#   - PromptTemplate especial
#   - parsear JSON manualmente
#
# El resultado será directamente un objeto
# AnalisisTexto.
# ==================================================

structured_llm = llm.with_structured_output(
    AnalisisTexto
)


# ==================================================
# 4. PUNTO DE ENTRADA DEL PROGRAMA
# ==================================================
# Este bloque solo se ejecuta cuando el archivo
# se ejecuta directamente.
#
# Si este archivo se importa desde otro script,
# este bloque NO se ejecutará.
# ==================================================

if __name__ == "__main__":

    # Texto que queremos analizar
    texto = """
    Me encantó la nueva película de acción,
    tiene efectos especiales increíbles.
    """

    # ==================================================
    # 5. PROMPT
    # ==================================================
    # Aquí damos instrucciones al modelo.
    #
    # Aunque el modelo ya conoce el esquema gracias
    # a AnalisisTexto, es buena práctica indicar
    # claramente lo que esperamos.
    # ==================================================

    prompt = f"""
    Analiza el siguiente texto y devuelve:

    - Un resumen breve.
    - El sentimiento (Positivo, Neutro o Negativo).
    - Entre 3 y 5 palabras clave.

    Texto:
    {texto}
    """

    try:

        # ==================================================
        # 6. INVOCAR EL MODELO
        # ==================================================
        # invoke() envía el prompt al modelo.
        #
        # El resultado NO es texto plano.
        #
        # LangChain automáticamente convierte la
        # respuesta en un objeto AnalisisTexto.
        # ==================================================

        resultado = structured_llm.invoke(prompt)

        print("✅ Análisis exitoso\n")

        # ==================================================
        # 7. ACCESO A LOS CAMPOS
        # ==================================================
        # Como resultado es un objeto Pydantic,
        # podemos acceder a sus atributos igual
        # que en cualquier clase de Python.
        # ==================================================

        print("Resumen:")
        print(resultado.resumen)

        print("\nSentimiento:")
        print(resultado.sentimiento)

        print("\nPalabras clave:")
        print(resultado.palabras_clave)

        # ==================================================
        # 8. CONVERTIR A JSON
        # ==================================================
        # model_dump_json() transforma el objeto
        # Pydantic en JSON.
        #
        # Muy útil para APIs, bases de datos,
        # archivos o integraciones.
        # ==================================================

        print("\nJSON:")
        print(resultado.model_dump_json(indent=2))

    except Exception as e:

        # ==================================================
        # 9. MANEJO DE ERRORES
        # ==================================================
        # Captura errores como:
        # - API Key inexistente
        # - Error de conexión
        # - Error de autenticación
        # - Problemas con el modelo
        # ==================================================

        print(f"❌ Error: {e}")