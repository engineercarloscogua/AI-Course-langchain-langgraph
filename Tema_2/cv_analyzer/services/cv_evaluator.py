# =====================================================
# IMPORTACIONES
# =====================================================

# Modelo de chat de OpenAI integrado con LangChain.
from langchain_openai import ChatOpenAI

# Modelo Pydantic que define la estructura de salida.
# El LLM deberá devolver exactamente este formato.
from models.cv_model import AnalisisCV

# Función que construye el prompt del sistema.
# Probablemente contiene instrucciones como:
# "Actúa como reclutador experto..."
from prompts.cv_prompts import crear_sistema_prompts


# =====================================================
# FUNCIÓN: CREAR EVALUADOR DE CV
# =====================================================
# Esta función construye toda la cadena de análisis
# y la devuelve lista para ser utilizada.
# =====================================================

def crear_evaluador_cv():

    # ---------------------------------------------
    # 1. Crear el modelo base
    # ---------------------------------------------
    # temperature=0.2 hace que las respuestas sean
    # más consistentes y menos creativas.
    #
    # Para tareas de RRHH y evaluación suele ser
    # mejor usar temperaturas bajas.
    # ---------------------------------------------

    modelo_base = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    # ---------------------------------------------
    # 2. Convertir el modelo en estructurado
    # ---------------------------------------------
    # Gracias a AnalisisCV, LangChain obligará al
    # modelo a responder siguiendo exactamente
    # la estructura definida en ese modelo.
    #
    # Ya no necesitamos parsers manuales.
    # ---------------------------------------------

    modelo_estructurado = modelo_base.with_structured_output(
        AnalisisCV
    )

    # ---------------------------------------------
    # 3. Crear el PromptTemplate
    # ---------------------------------------------
    # Esta función probablemente devuelve algo como:
    #
    # System:
    # "Eres un reclutador experto..."
    #
    # Human:
    # "CV: {texto_cv}
    #  Vacante: {descripcion_puesto}"
    # ---------------------------------------------

    chat_prompt = crear_sistema_prompts()

    # ---------------------------------------------
    # 4. Construir la cadena LCEL
    # ---------------------------------------------
    # El operador | conecta componentes.
    #
    # Flujo:
    #
    # Prompt
    #    ↓
    # Modelo OpenAI
    #    ↓
    # Objeto AnalisisCV
    #
    # ---------------------------------------------

    cadena_evaluacion = chat_prompt | modelo_estructurado

    # Devuelve la cadena completa
    return cadena_evaluacion


# =====================================================
# FUNCIÓN PRINCIPAL DE EVALUACIÓN
# =====================================================
# Recibe:
#
# texto_cv
#   Texto extraído del PDF.
#
# descripcion_puesto
#   Perfil o vacante a comparar.
#
# Devuelve:
#
# AnalisisCV
#
# =====================================================
# -> es un notación d elo que deberia devolver python
def evaluar_candidato( texto_cv: str, descripcion_puesto: str) -> AnalisisCV:

    try:

        # -----------------------------------------
        # 1. Crear la cadena de evaluación
        # -----------------------------------------

        cadena_evaluacion = crear_evaluador_cv()

        # -----------------------------------------
        # 2. Ejecutar la cadena
        # -----------------------------------------
        # invoke() envía la información al modelo.
        #
        # Los nombres de las variables deben coincidir
        # con los definidos dentro del PromptTemplate.
        #
        # texto_cv      -> contenido del CV
        # descripcion_puesto -> requisitos vacante
        # -----------------------------------------

        resultado = cadena_evaluacion.invoke({
            "texto_cv": texto_cv,
            "descripcion_puesto": descripcion_puesto
        })

        # -----------------------------------------
        # 3. Retornar el análisis generado por IA
        # -----------------------------------------
        #
        # resultado ya es un objeto AnalisisCV
        #
        # Ejemplo:
        #
        # resultado.nombre_candidato
        # resultado.porcentaje_ajuste
        # resultado.fortalezas
        #
        # -----------------------------------------

        return resultado

    except Exception as e:

        # -----------------------------------------
        # MANEJO DE ERRORES
        # -----------------------------------------
        #
        # Este bloque se ejecuta si ocurre:
        #
        # - Error de API
        # - PDF ilegible
        # - Timeout
        # - Error de autenticación
        # - Error de conexión
        # - Error de formato
        #
        # En lugar de detener el programa,
        # devolvemos un objeto AnalisisCV válido.
        # -----------------------------------------

        return AnalisisCV(

            # Nombre genérico indicando error
            nombre_candidato="Error en procesamiento.",

            # Valor por defecto
            experiencia_años=0,

            # Lista indicando el problema
            habilidades_clave=[
                "Error al procesar CV"
            ],

            # Educación desconocida
            education="No se puede determinar.",

            # Experiencia no analizada
            experiencia_relevante=
                "Error durante el análisis.",

            # Mensaje para el reclutador
            fotalezas=[
                "Requiere revisión manual del CV"
            ],

            # Recomendación
            areas_mejora=[
                "Verificar formato y legibilidad del PDF"
            ],

            # Sin puntuación debido al error
            porcetaje_ajuste=0
        )