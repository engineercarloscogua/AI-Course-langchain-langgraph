# ==============================================================================
# SISTEMA RAG (Retrieval-Augmented Generation) - ASISTENTE LEGAL DE CONTRATOS
# ==============================================================================
# Este archivo implementa toda la arquitectura del sistema RAG. Su función es:
# 1. Conectarse a la base de datos vectorial Chroma.
# 2. Utilizar un modelo de lenguaje (LLM) para expandir la consulta original (Multi-Query).
# 3. Recuperar los fragmentos de documentos legales más relevantes usando búsqueda MMR.
# 4. Formatear y alimentar el contexto del prompt para que el LLM genere la respuesta final.
# ==============================================================================

# --- IMPORTACIONES DE LIBRERÍAS ---

# Conector de LangChain para usar ChromaDB como base de datos de vectores
from langchain_community.vectorstores import Chroma

# Clases oficiales de LangChain para generar vectores (embeddings) y chatear con modelos de OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Clase de LangChain para estructurar y rellenar plantillas de prompts de manera dinámica
from langchain_core.prompts import PromptTemplate

# RunnablePassthrough permite transferir datos a través del pipeline de LangChain sin modificarlos
from langchain_core.runnables import RunnablePassthrough

# Convertidor simple que toma la salida cruda del LLM y la extrae como una cadena de texto limpia
from langchain_core.output_parsers import StrOutputParser

# Recuperador avanzado que usa un LLM para redactar múltiples variaciones semánticas de una consulta
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

#========RECUPERACIÓN HIBRIDA AVANZADA===================
from langchain_classic.retrievers import EnsembleRetriever

# Streamlit se utiliza aquí únicamente para almacenar recursos pesados en caché local (optimizando la carga)
import streamlit as st

# Importamos las variables de configuración global definidas en config.py (rutas, modelos, parámetros)
from config import *

# Importamos las plantillas de prompts (RAG_TEMPLATE, MULTI_QUERY_PROMPT, etc.) desde prompts.py
from prompts import * 


# --- INICIALIZACIÓN DEL SISTEMA RAG ---

# Decorador de Streamlit para asegurar que esta función solo se ejecute una vez
# Almacena en caché los objetos creados (Chroma, LLMs, Retriever) para no recargarlos en cada consulta del usuario.
@st.cache_resource
def inizialize_rag_system():
    
    # 1. Configuración y conexión al Vector Store (ChromaDB)
    vector_store = Chroma(
        # Especificamos el modelo que transformará la consulta del usuario a vectores
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        # Ruta absoluta en el disco donde se encuentra guardada la base de datos vectorial
        persist_directory=CHROMA_DB_PATH
    )
    
    # 2. Configuración de los Modelos de Lenguaje (LLMs)
    # Nota: Usamos temperature=0 para asegurar respuestas más consistentes, lógicas y deterministas.
    # LLM utilizado para reescribir y refinar la pregunta del usuario en múltiples variantes
    llm_queries = ChatOpenAI(model=QUERY_MODEL, temperature=0)
    # LLM principal y más potente para generar la respuesta legal definitiva basándose en el contexto
    llm_generation = ChatOpenAI(model=GENERATION_MODEL, temperature=0)
    
    # 3. Configuración del Recuperador Base (Base Retriever)
    # Convertimos la base de datos de vectores en un componente que puede buscar y devolver documentos.
    # Usamos la búsqueda MMR (Maximal Margin Relevance) en lugar de similitud simple por coseno.
    # Esto ayuda a balancear la similitud con la diversidad de información para evitar recuperar textos repetitivos.
    base_retriever = vector_store.as_retriever(
        search_type=SEARCH_TYPE, # Definido como "mmr" en config.py
        search_kwargs={
            "k": SEARCH_K,                    # Número de documentos finales procesados que enviaremos al LLM (ej. 2)
            "lambda_mult": MMR_DIVERSITY_LAMBDA, # Factor de diversidad (0 a 1). 0.7 prioriza balance similitud/diversidad.
            "fetch_k": MMR_FETCH_K            # Número de documentos iniciales que recupera para aplicar la fórmula MMR (ej. 20)
        }
    )
    
    #===RETRIEVER ADICIONAL PARA RECUPERACIÓN HIBRIDA ==== COSENO SIMILARITY
    similarity_retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = {
            "k": SEARCH_K,        
        }
    )
    
    # 4. Configuración del Multi-Query Retriever (Retriever Avanzado)
    # Cargamos el prompt personalizado que enseña al LLM cómo reescribir la pregunta legal de 3 formas distintas
    multi_query_prompt = PromptTemplate.from_template(MULTI_QUERY_PROMPT)
    
    # Creamos el recuperador avanzado asociándole el retriever base, el modelo corrector y su prompt
    mmr_multi_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,     # El motor de búsqueda física (Chroma)
        llm=llm_queries,             # El LLM que generará las 3 variantes de la pregunta
        prompt=multi_query_prompt    # Las instrucciones de formulación de preguntas alternativas
    ) 
    
    #--------ENSEMBLE RETRIEVER HIBRID-----MMR + COSENO-----
    if ENABLE_HYBRID_SEARCH:
        ensemble_retriever = EnsembleRetriever(
            retrievers = [mmr_multi_retriever, similarity_retriever],
            #mayor peso a MMR que a Coseno
            weights = [0.7 , 0.3],
            #NO DEVUELVE NINGUN DOCUMENTO RELEVANT SI LA SIMIULD Y LA CONSULTA SON MENOR A LO QUE ESTA EN CONFIG
            similarity_threshold = SIMILARITY_THRESHOLD
        )
        #recuperación final
        final_retreiever = ensemble_retriever
    else:
        # si en config no esta activo entonces solo usa el multi retriever sin el hibrido
        final_retreiever = mmr_multi_retriever
    
    
    
    # 5. Configuración del Prompt de Respuesta RAG
    # Cargamos la plantilla de prompt final donde se insertarán la pregunta original y el contexto recuperado
    prompt = PromptTemplate.from_template(RAG_TEMPLATE)
    
    # 6. Función Auxiliar para Procesar y Formatear los Documentos Recuperados
    def format_docs(docs):
        """
        Recibe una lista de objetos Document y los une en un string formateado.
        Limpia los nombres de los archivos fuente y añade la numeración de páginas para facilitar la lectura del LLM.
        """
        formatted = []
        for i, doc in enumerate(docs, 1):
            header = f"[Fragmento {i}]"
            # Si el documento tiene metadatos asociados, extraemos su información
            if doc.metadata:
                # Limpiamos la ruta del archivo para mostrar solo el nombre del archivo PDF
                if 'source' in doc.metadata:
                    source = doc.metadata['source'].split("\\")[-1] if '\\' in doc.metadata["source"] else doc.metadata['source']
                    header += f" fuente {source}"
                # Agregamos la página del documento si está disponible
                if 'page' in doc.metadata:
                    header += f" - Pagina: {doc.metadata['page']}"
            
            # Limpiamos espacios en blanco redundantes y unimos el contenido en texto plano limpio
            content = " ".join(doc.page_content.split())
            formatted.append(f"{header}\n {content}")
            
        # Retorna todos los fragmentos consolidados en un único bloque de texto separado por saltos de línea
        return "\n\n".join(formatted)
    
    # 7. Construcción de la Cadena RAG mediante LCEL (LangChain Expression Language)
    # La tubería (pipeline) define paso a paso cómo viajan los datos:
    # Pregunta -> Recuperación y Formateo de Fragmentos -> Inserción en Prompt -> LLM -> Cadena de texto final.
    rag_chain = (
        # Definición de las variables que el Prompt final necesita recibir:
        {   
            # Toma la pregunta de entrada, la envía al MultiQueryRetriever y pasa los resultados por format_docs
            #"context": mmr_multi_retriever | format_docs,
            #Aplicando retreiever hibrido mmr + coseno
            "context": final_retreiever | format_docs,
            # Mantiene la pregunta original intacta sin modificaciones
            "question": RunnablePassthrough(),
        }
        # Pasa el diccionario anterior con {"context", "question"} al template del prompt
        | prompt 
        # Envía el prompt formateado al LLM principal de generación de respuestas (GPT-4o)
        | llm_generation 
        # Parsea los bytes de salida del modelo a un String estándar de Python
        | StrOutputParser()
    )
    
    # Retornamos tanto la cadena completa (para ejecutar consultas) como el retriever avanzado (para extraer metadatos)
    return rag_chain, mmr_multi_retriever 


# --- FUNCIÓN PRINCIPAL DE CONSULTA ---

def query_rag(question):
    """
    Función expuesta para ser consumida por Streamlit u otros scripts.
    Recibe la consulta del usuario, ejecuta el pipeline RAG y retorna la respuesta con las referencias.
    """
    try:
        # Inicializa la cadena RAG y el recuperador optimizado en caché
        rag_chain, retriever = inizialize_rag_system()
        
        # 1. Ejecución del pipeline completo RAG para obtener la respuesta final del LLM
        response = rag_chain.invoke(question)
        
        # 2. Recuperación aislada de los fragmentos de documentos utilizados para mostrarlos en el frontend
        docs = retriever.invoke(question)
        
        # 3. Estructuración de metadatos para la interfaz web (Streamlit)
        docs_info = []
        for i, doc in enumerate(docs[:SEARCH_K], 1):
            info = {
                "fragmento": i,
                # Limitamos el texto del fragmento a 1000 caracteres para no saturar visualmente el panel lateral
                "contenido": doc.page_content[:1000] + "..." if len(doc.page_content) > 1000 else doc.page_content,
                # Extrae el nombre del archivo del metadato de origen
                "fuente": doc.metadata.get('source', 'Fuente No especificada').split("\\")[-1],
                # Extrae el número de página del documento original
                "pagina": doc.metadata.get('page', 'Pagina No especificada')
            }
            # Agrega los metadatos de este fragmento a la lista que será retornada
            docs_info.append(info)
            
        # Devolvemos exitosamente la respuesta textual y la lista estructurada de metadatos de los documentos
        return response, docs_info
        
    except Exception as e:
        # En caso de cualquier error durante el proceso, capturamos la excepción y devolvemos un mensaje seguro
        error_msg = f"Error al procesar la pregunta: {str(e)}"
        return error_msg, []


# --- FUNCIÓN AUXILIAR DE INFORMACIÓN ---

def get_retriever_info():
    """
    Retorna los datos de configuración actuales del sistema de recuperación para mostrarlos en el sidebar de Streamlit.
    """
    return {
        "tipo": f"{SEARCH_TYPE.upper()} + MultyQuery" + (" +  Hybrid" if ENABLE_HYBRID_SEARCH else ""),      # Tipo de búsqueda (ej. MMR)
        "documentos": SEARCH_K,                # Número final de fragmentos enviados al LLM
        "diversidad": MMR_DIVERSITY_LAMBDA,   # Factor de diversidad MMR
        "candidatos": MMR_FETCH_K,             # Número inicial de fragmentos extraídos de ChromaDB
        "umbral": SIMILARITY_THRESHOLD if ENABLE_HYBRID_SEARCH else "N/A"                    # Umbral de puntuación (no utilizado en MMR tradicional)
    }