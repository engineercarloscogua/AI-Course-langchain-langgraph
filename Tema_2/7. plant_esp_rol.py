# ==========================================================
# IMPORTACIÓN DE CLASES
# ==========================================================

# ChatPromptTemplate:
# Permite combinar varios mensajes (sistema, usuario, etc.)
# para construir un prompt completo para un LLM.
#
# SystemMessagePromptTemplate:
# Crea mensajes de sistema. Son instrucciones que definen
# el comportamiento del modelo.
#
# HumanMessagePromptTemplate:
# Crea mensajes que representan la entrada del usuario.
#
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# ==========================================================
# MENSAJE DEL SISTEMA
# ==========================================================

# from_template() crea una plantilla reutilizable.
#
# Las palabras entre llaves {} son variables dinámicas.
#
# Más adelante podremos reemplazar:
# {rol}
# {especialidad}
# {tono}
#
plantilla_sistema = SystemMessagePromptTemplate.from_template(
    "Eres un {rol} especializado en {especialidad}. "
    "Responde de manera {tono}"
)

# ==========================================================
# MENSAJE DEL USUARIO
# ==========================================================

# Esta plantilla representa lo que preguntará el usuario.
#
# Las variables son:
# {tema}
# {pregunta}
#
plantilla_humano = HumanMessagePromptTemplate.from_template(
    "Mi pregunta sobre {tema} es: {pregunta}"
)

# ==========================================================
# CONSTRUCCIÓN DEL PROMPT COMPLETO
# ==========================================================

# from_messages() recibe una lista de mensajes.
#
# El orden es importante:
# 1. Sistema
# 2. Usuario
#
# El modelo leerá primero las instrucciones
# y después la pregunta.
# PLANTILLA FINAL, esta es la que se lenvia al LLM

chat_prompt = ChatPromptTemplate.from_messages(
    [
        plantilla_sistema,
        plantilla_humano
    ]
)

# ==========================================================
# RELLENAR LAS VARIABLES DEL PROMPT
# ==========================================================

# format_messages() reemplaza las variables
# definidas anteriormente.
#
# Por ejemplo:
#
# {rol} -> nutricionista
# {especialidad} -> dietas veganas
#
# El resultado NO es texto plano.
# Devuelve una lista de objetos Message.
#
mensajes = chat_prompt.format_messages(
    rol="nutricionista",
    especialidad="dietas veganas",
    tono="profesional pero accesible",
    tema="proteínas vegetales",
    pregunta="¿Cuáles son las mejores fuentes de proteína para un niño de 10 años?"
)

# ==========================================================
# VISUALIZAR LOS MENSAJES GENERADOS
# ==========================================================

# 'mensajes' es una lista que contiene:
#
# [SystemMessage(...),
#  HumanMessage(...)]
#
# Recorremos cada mensaje usando un ciclo for.
#
for m in mensajes:

    # .content devuelve únicamente el texto
    # contenido dentro del mensaje.
    #
    # Sin .content veríamos el objeto completo.
    #
    print(m.content)
