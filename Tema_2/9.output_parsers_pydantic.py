# ==========================================================
# IMPORTACIÓN DE LIBRERÍAS
# ==========================================================

# BaseModel:
# Clase base de Pydantic que permite crear modelos de datos
# con validación automática.
#
# Field:
# Permite agregar descripciones y configuraciones adicionales
# a cada atributo del modelo.
#
from pydantic import BaseModel, Field

# ChatOpenAI:
# Clase que permite conectarse a los modelos de OpenAI
# desde LangChain.
#
from langchain_openai import ChatOpenAI

# Literal:
# Restringe los posibles valores que puede tomar un campo.
#
from typing import Literal


# ==========================================================
# DEFINICIÓN DEL MODELO DE SALIDA
# ==========================================================

# Esta clase define EXACTAMENTE la estructura
# que queremos recibir del modelo.
#
# El LLM intentará devolver un objeto con:
# - resumen
# - sentimiento
#
class AnalisisTexto(BaseModel):

    # Campo para almacenar un resumen breve.
    resumen: str = Field(
        description="Resumen breve del texto."
    )

    # Campo para almacenar el sentimiento.
    #
    # Literal obliga al modelo a escoger únicamente
    # uno de estos tres valores.
    #
    sentimiento: Literal[
        "Positivo",
        "Negativo",
        "Neutro"
    ] = Field(
        description="Sentimiento identificado en el texto."
    )


# ==========================================================
# CREACIÓN DEL MODELO DE IA
# ==========================================================

# model:
# Nombre del modelo que se utilizará.
#
# temperature:
# Controla la creatividad.
#
# 0   = respuestas más deterministas.
# 1   = respuestas más creativas.
#
# Para clasificación se recomienda usar 0.
#
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ==========================================================
# CONFIGURAR SALIDA ESTRUCTURADA
# ==========================================================

# with_structured_output()
#
# Le indica a LangChain:
#
# "Quiero que la respuesta tenga la estructura
# definida por la clase AnalisisTexto."
#
# Internamente LangChain genera instrucciones
# especiales para que el modelo responda
# siguiendo ese formato.
#
structured_llm = llm.with_structured_output(
    AnalisisTexto
)


# ==========================================================
# TEXTO QUE VAMOS A ANALIZAR
# ==========================================================

texto_prueba = """
Me encantó la película de acción,
tiene muchos efectos especiales y es perfecta,
me hace muy feliz.
"""


# ==========================================================
# CREACIÓN DEL PROMPT
# ==========================================================

# f-string:
#
# Permite insertar variables dentro del texto.
#
# Si NO colocas la letra f delante de las comillas:
#
# "Analiza {texto_prueba}"
#
# el modelo verá literalmente:
#
# {texto_prueba}
#
# y no el contenido de la variable.
#
prompt = f"""
Analiza el siguiente texto y determina:

1. Un resumen breve.
2. El sentimiento general.

Texto:
{texto_prueba}
"""


# ==========================================================
# VISUALIZAR EL PROMPT (OPCIONAL)
# ==========================================================

# Muy útil para depuración.
#
# Permite verificar exactamente qué texto
# está recibiendo el modelo.
#
print("PROMPT ENVIADO AL MODELO:")
print(prompt)


# ==========================================================
# LLAMADA AL MODELO
# ==========================================================

# invoke()
#
# Envía el prompt al modelo.
#
# Como configuramos salida estructurada,
# NO recibiremos texto plano.
#
# Recibiremos un objeto AnalisisTexto.
#
resultado = structured_llm.invoke(prompt)


# ==========================================================
# MOSTRAR RESULTADO COMPLETO
# ==========================================================

print("\nRESULTADO COMPLETO:")
print(resultado)


# ==========================================================
# ACCEDER A CADA CAMPO
# ==========================================================

# Como resultado es un objeto AnalisisTexto,
# podemos acceder a sus atributos como cualquier clase.
#
print("\nResumen:")
print(resultado.resumen)

print("\nSentimiento:")
print(resultado.sentimiento)