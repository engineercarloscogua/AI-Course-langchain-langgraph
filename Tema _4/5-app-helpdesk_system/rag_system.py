# ==============================================================================
# SISTEMA DE RECUPERACIÓN Y GENERACIÓN AUMENTADA (RAG) - HELPDESK SYSTEM
# ==============================================================================
# Este archivo implementa la clase VectorRAGSystem para consultar la BD vectorial:
# Paso 1: Importación de dependencias de LangChain, OpenAI y configuración.
# Paso 2: Definición de la clase VectorRAGSystem e inicialización de componentes.
# Paso 3: Carga del vectorstore ChromaDB y configuración de MultiQueryRetriever.
# Paso 4: Definición del Prompt personalizado para MultiQueryRetriever.
# Paso 5: Método de búsqueda semántica (buscar) y extracción de contexto y fuentes.
# Paso 6: Generación de respuesta final con el modelo LLM basándose en contexto.
# Paso 7: Cálculo de la métrica de confianza basada en palabras clave y volumen.
# ==============================================================================

# ------------------------------------------------------------------------------
# PASO 1: IMPORTACIÓN DE LIBRERÍAS Y MÓDULOS
# ------------------------------------------------------------------------------
from pathlib import Path
import logging
from typing import List, Dict, Any

# Intento de importación preferida para ChromaDB (estándar moderno) con fallback a community
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

# Modelos de OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Importación robusta de MultiQueryRetriever con compatibilidad multi-versión
try:
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever
except ImportError:
    try:
        from langchain.retrievers.multi_query import MultiQueryRetriever
    except ImportError:
        from langchain.retrievers import MultiQueryRetriever

# Importación de variables globales de configuración
from config import CHROMADB_PATH, EMBEDDINGS_MODEL, LLM_MODEL


# ------------------------------------------------------------------------------
# PASO 2: DEFINICIÓN DE LA CLASE VECTORRAGSYSTEM E INICIALIZACIÓN
# ------------------------------------------------------------------------------
class VectorRAGSystem:
    """Sistema RAG avanzado con ChromaDB y MultiQueryRetriever."""
    
    def __init__(self, chroma_path: str = CHROMADB_PATH):
        """Inicialización de los componentes del sistema RAG."""
        # Ruta del directorio donde se encuentra guardada la BD vectorial
        self.chroma_path = Path(chroma_path)
        
        # Modelo de embeddings de OpenAI (convertidor de texto a vectores)
        self.embeddings = OpenAIEmbeddings(model=EMBEDDINGS_MODEL)
        
        # Modelo LLM de OpenAI para generación de respuestas y variación de queries
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0.0)
        
        # Atributos para almacenar la base de datos y el recuperador
        self.vectorstore = None
        self.retriever = None
        
        # Configurar logging para el seguimiento del MultiQueryRetriever
        logging.basicConfig()
        logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
        
        # Cargar la base de datos vectorial automáticamente
        self._load_vectorstore()

    # --------------------------------------------------------------------------
    # PASO 3: CARGA DE LA BD VECTORIAL Y CONFIGURACIÓN DEL RETRIEVER
    # --------------------------------------------------------------------------
    def _load_vectorstore(self):
        """Carga el vectorstore de ChromaDB y configura el MultiQueryRetriever."""
        try:
            # Verificar si existe físicamente el directorio del vectorstore
            if not self.chroma_path.exists():
                print(f"[WARN] Vectorstore no encontrado en {self.chroma_path}")
                return
                
            # Cargar la base de datos vectorial existente
            self.vectorstore = Chroma(
                persist_directory=str(self.chroma_path),
                embedding_function=self.embeddings,
                collection_name="helpdesk_knowledge"
            )
            
            # Inicializar el recuperador MultiQueryRetriever (genera 3 variaciones de la consulta)
            self.retriever = MultiQueryRetriever.from_llm(  
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 4}  # Recuperar top 4 fragmentos más relevantes
                ),
                llm=self.llm,
                prompt=self._get_multi_query_prompt()
            )
            
            print("[OK] VectorRAGSystem inicializado correctamente")
        
        except Exception as e:
            print(f"[ERROR] Error cargando vectorstore: {str(e)}")
            self.vectorstore = None
            self.retriever = None

    # --------------------------------------------------------------------------
    # PASO 4: PLANTILLA DE PROMPT PARA MULTIQUERYRETRIEVER
    # --------------------------------------------------------------------------
    def _get_multi_query_prompt(self) -> ChatPromptTemplate:
        """Genera el prompt personalizado para diversificar la consulta del usuario."""
        return ChatPromptTemplate.from_template(
            """Eres un asistente de helpdesk experto. Tu tarea es generar múltiples 
            versiones de la consulta del usuario para recuperar documentos relevantes de una 
            base de conocimiento de soporte técnico.
    
            Genera 3 versiones diferentes de la consulta original, considerando:
            - Sinónimos técnicos
            - Diferentes formas de expresar el mismo problema
            - Variaciones en terminología de helpdesk

            Consulta original: {question}

            Versiones alternativas:"""
        )

    # --------------------------------------------------------------------------
    # PASO 5: BÚSQUEDA SEMÁNTICA Y RECUPERACIÓN DE DOCUMENTOS
    # --------------------------------------------------------------------------
    def buscar(self, consulta: str) -> Dict[str, Any]:
        """Ejecuta la búsqueda semántica y genera la respuesta contextualizada."""
        # Verificar disponibilidad del recuperador
        if not self.retriever:
            return {
                "respuesta": "Sistema RAG no disponible. Verifique la configuración.",
                "confianza": 0.0,
                "fuentes": []
            }
        
        try:
            # Ejecutar MultiQueryRetriever mediante el método estándar .invoke()
            documentos = self.retriever.invoke(consulta)
            
            if not documentos:
                return {
                    "respuesta": "No encontré información relevante en la base de conocimiento.",
                    "confianza": 0.1,
                    "fuentes": []
                }
            
            contexto_partes = []
            fuentes = []
            
            # Formatear el contexto con los top 3 documentos
            for i, doc in enumerate(documentos[:3]):
                contenido = doc.page_content.strip()
                if contenido:
                    contexto_partes.append(f"Documento {i+1}: {contenido}")
                    filename = doc.metadata.get('filename', f'doc_{i+1}')
                    if filename not in fuentes:
                        fuentes.append(filename)
            
            if not contexto_partes:
                return {
                    "respuesta": "Documentos encontrados pero sin contenido útil.",
                    "confianza": 0.2,
                    "fuentes": fuentes
                }
            
            contexto = "\n\n".join(contexto_partes)
            
            # Generar la respuesta final usando el LLM y calcular confianza
            respuesta = self._generar_respuesta(consulta, contexto)
            confianza = self._calcular_confianza(consulta, documentos)
            
            return {
                "respuesta": respuesta,
                "confianza": confianza,
                "fuentes": fuentes
            }
            
        except Exception as e:
            print(f"[ERROR] Error en búsqueda RAG: {str(e)}")
            return {
                "respuesta": f"Error interno en la búsqueda: {str(e)}",
                "confianza": 0.0,
                "fuentes": []
            }

    # --------------------------------------------------------------------------
    # PASO 6: GENERACIÓN DE RESPUESTA CON EL MODELO LLM
    # --------------------------------------------------------------------------
    def _generar_respuesta(self, consulta: str, contexto: str) -> str:
        """Genera una respuesta basada exclusivamente en el contexto recuperado."""
        prompt = ChatPromptTemplate.from_template(
            """Eres un asistente de helpdesk experto. Responde a la consulta del usuario 
            basándote únicamente en el contexto proporcionado de la base de conocimiento.

            Instrucciones:
            - Proporciona una respuesta clara, directa y útil
            - Si el contexto no contiene información suficiente, dilo claramente
            - Mantén un tono profesional pero amigable
            - No inventes información que no esté en el contexto

            Contexto de la base de conocimiento:
            {contexto}

            Consulta del usuario: {consulta}

            Respuesta:"""
        )
        
        try:
            response = self.llm.invoke(prompt.format(consulta=consulta, contexto=contexto))
            return response.content.strip()
        except Exception as e:
            print(f"[ERROR] Error generando respuesta: {str(e)}")
            return f"Error generando respuesta: {str(e)}"
    
    # --------------------------------------------------------------------------
    # PASO 7: CÁLCULO DE CONFIANZA DE LA RESPUESTA
    # --------------------------------------------------------------------------
    def _calcular_confianza(self, consulta: str, documentos: List) -> float:
        """Calcula una métrica de confianza basada en solapamiento de palabras clave y volumen."""
        if not documentos:
            return 0.0
        
        num_docs = len(documentos)
        palabras_consulta = set(consulta.lower().split())
        puntuacion_relevancia = 0
        total_contenido = 0
        
        for doc in documentos[:3]:
            contenido = doc.page_content.lower()
            total_contenido += len(contenido.split())
            
            coincidencias = sum(1 for palabra in palabras_consulta 
                              if palabra in contenido and len(palabra) > 2)
            puntuacion_relevancia += coincidencias
        
        if palabras_consulta and total_contenido > 0:
            confianza_base = min(puntuacion_relevancia / len(palabras_consulta), 1.0)
            bonus_documentos = min(num_docs / 4.0, 0.2)
            bonus_contenido = min(total_contenido / 1000.0, 0.1)
            
            confianza_final = min(confianza_base + bonus_documentos + bonus_contenido, 1.0)
            return round(confianza_final, 2)
        
        return 0.3
