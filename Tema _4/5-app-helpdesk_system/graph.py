# ==============================================================================
# DEFINICIÓN DEL GRAFO Y ESTADO (LANGGRAPH) - HELPDESK SYSTEM
# ==============================================================================
# Este archivo define la estructura del grafo de flujo de trabajo para Helpdesk:
# Paso 1: Importación de dependencias de LangChain, LangGraph y módulos locales.
# Paso 2: Definición del esquema del Estado del Grafo (HelpdeskState).
# Paso 3: Definición de la clase HelpdeskGraph e inicialización de LLM y RAG.
# Paso 4: Nodos del grafo (procesar_rag, clasificar, escalar, etc.).
# Paso 5: Funciones de enrutamiento condicional (decisión automática o escalado).
# Paso 6: Construcción y estructura del Grafo (StateGraph).
# Paso 7: Compilación del grafo con persistencia y Human-in-the-Loop.
# Paso 8: Función constructora auxiliar (crear_helpdesk).
# ==============================================================================

# ------------------------------------------------------------------------------
# PASO 1: IMPORTACIÓN DE LIBRERÍAS Y MÓDULOS
# ------------------------------------------------------------------------------
import sqlite3
from typing import TypedDict, Annotated, Optional
from operator import add

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START

# Checkpointer con fallback automático entre SqliteSaver y MemorySaver
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    HAS_SQLITE_SAVER = True
except ImportError:
    try:
        from langgraph.checkpoint.sqlite.sqlite3 import SqliteSaver
        HAS_SQLITE_SAVER = True
    except ImportError:
        HAS_SQLITE_SAVER = False

from langgraph.checkpoint.memory import MemorySaver

# Importaciones de módulos locales
from rag_system import VectorRAGSystem
from config import CHROMADB_PATH, LLM_MODEL

# ------------------------------------------------------------------------------
# PASO 2: DEFINICIÓN DEL ESTADO DEL GRAFO (STATE)
# Esquema TypedDict que define la estructura de datos compartida en el grafo.
# ------------------------------------------------------------------------------
class HelpdeskState(TypedDict):
    # Consulta original ingresada por el usuario
    consulta: str
    # Categoría asignada a la consulta ("automatico" o "escalado")
    categoria: str
    # Respuesta basada en los documentos de la BD vectorial
    respuesta_rag: Optional[str]
    # Nivel de confianza numérico de la búsqueda semántica
    confianza: float
    # Lista de nombres de los documentos fuente utilizados
    fuentes: list[str]
    # Contexto de texto recuperado de la base de conocimiento
    contexto_rag: Optional[str]
    # Indicador booleano de si la consulta requiere intervención humana
    requiere_humano: bool
    # Respuesta proporcionada por un agente humano (si aplica)
    respuesta_humano: Optional[str]
    # Respuesta final procesada que se entregará al usuario
    respuesta_final: Optional[str]
    # Historial acumulativo de eventos y mensajes de la conversación
    historial: Annotated[list[str], add]

# ------------------------------------------------------------------------------
# PASO 3: DEFINICIÓN DE LA CLASE HELPDESKGRAPH E INICIALIZACIÓN
# ------------------------------------------------------------------------------
class HelpdeskGraph:
    """Grafo interactivo del sistema Helpdesk con RAG y Human-in-the-Loop."""
    
    def __init__(self):
        """Inicialización del modelo LLM, sistema RAG y compilador."""
        # Modelo de lenguaje de OpenAI para razonamiento y respuestas
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1)
        # Instancia del sistema RAG conectado a ChromaDB
        self.rag = VectorRAGSystem(chroma_path=CHROMADB_PATH)
        # Objeto del grafo inicializado en None
        self.graph = None

    # --------------------------------------------------------------------------
    # PASO 4: NODOS DEL GRAFO
    # --------------------------------------------------------------------------
    def procesar_rag(self, state: HelpdeskState) -> dict:
        """Nodo 1: Busca información en la base de conocimiento usando el sistema RAG."""
        consulta = state["consulta"]
        resultado = self.rag.buscar(consulta)
        
        return {
            "respuesta_rag": resultado.get("respuesta", ""),
            "confianza": resultado.get("confianza", 0.0),
            "fuentes": resultado.get("fuentes", []),
            "contexto_rag": resultado.get("respuesta", ""),
            "historial": [
                "RAG ejecutado con multiquery",
                f"Consulta original: {consulta}",
                f"Documentos recuperados: {resultado.get('fuentes', [])}",
                f"Respuesta generada: {resultado.get('respuesta', '')}",
                f"Confianza: {resultado.get('confianza', 0.0)}"
            ]
        }

    def clasificar_con_contexto(self, state: HelpdeskState) -> dict:
        """Nodo 2: Evalúa si la consulta se puede resolver de forma automática o requiere escalado."""
        consulta = state["consulta"]
        contexto = state.get("contexto_rag", "")
        confianza = state.get("confianza", 0)

        prompt = ChatPromptTemplate.from_template(
            """Analiza esta consulta de helpdesk y decide si puede responderse automáticamente o necesita escalado:

CONSULTA DEL USUARIO: {consulta}

INFORMACIÓN ENCONTRADA EN LA BASE DE CONOCIMIENTO:
{contexto_rag}

CONFIANZA DE LA BÚSQUEDA: {confianza}

Criterios de decisión:
- AUTOMATICO: Si la información de la BD responde completamente la consulta, 
  tiene buena confianza (>0.6), y es un tema estándar/procedimiento conocido.
  
- ESCALADO: Si la información es insuficiente, confianza baja, problema complejo/único,
  requiere acceso a sistemas internos, o involucra decisiones de negocio.

Responde solo con "automatico" o "escalado" y una breve justificación (máximo 20 palabras):"""
        )
    
        try:
            response = self.llm.invoke(
                prompt.format(
                    consulta=consulta,
                    contexto_rag=contexto,
                    confianza=confianza
                )
            )
            content = response.content.strip().lower()
            
            if "automatico" in content or "automático" in content:
                categoria = "automatico"
            elif "escalado" in content:
                categoria = "escalado"               
            else:
                categoria = "automatico" if confianza >= 0.6 else "escalado"           
            
            return {
                "categoria": categoria,
                "historial": [
                    f"Clasificación con contexto: {categoria}",
                    f"Justificación: {response.content}"
                ]
            }
        except Exception as e:
            categoria = "automatico" if confianza >= 0.6 else "escalado"
            return {
                "categoria": categoria,
                "historial": [
                    f"Error al clasificar usando confianza: {confianza} ({str(e)})"
                ]                 
            }

    def preparar_escalado(self, state: HelpdeskState) -> dict:
        """Nodo 3: Marca el ticket para revisión por un agente humano."""
        return {
            "requiere_humano": True,
            "historial": ["Escalado a agente humano - esperando intervención"]
        }

    def procesar_respuesta_humano(self, state: HelpdeskState) -> dict:
        """Nodo 4: Procesa y asigna la respuesta redactada por el operador humano."""
        respuesta_humano = state.get("respuesta_humano", "")
        if respuesta_humano:
            return {
                "respuesta_final": respuesta_humano,
                "historial": ["Agente humano proporcionó respuesta"]
            }
        return {
            "historial": ["Esperando respuesta del agente humano"]
        }

    def generar_respuesta_final(self, state: HelpdeskState) -> dict:
        """Nodo 5: Entrega la respuesta final formateada al usuario."""
        if state.get("respuesta_final"):
            return {
                "respuesta_final": state.get("respuesta_final"),
                "historial": ["Respuesta final generada por agente humano"]
            }
    
        respuesta_rag = state.get("respuesta_rag", "")
        fuentes = state.get("fuentes", [])

        respuesta_final = respuesta_rag
        if fuentes:
            fuentes_texto = ", ".join(fuentes)
            respuesta_final += f"\n\nFuentes consultadas: {fuentes_texto}"
        
        return {
            "respuesta_final": respuesta_final,
            "historial": ["Respuesta final generada por AI"]
        }

    # --------------------------------------------------------------------------
    # PASO 5: FUNCIONES DE ENRUTAMIENTO CONDICIONAL
    # --------------------------------------------------------------------------
    def decidir_desde_clasificacion(self, state: HelpdeskState) -> str:
        """Decide el camino tras clasificar: respuesta directa o escalado."""
        categoria = state.get("categoria", "escalado")
        if categoria == "automatico":
            return "respuesta_final" 
        else:
            return "escalar"

    def decidir_desde_humano(self, state: HelpdeskState) -> str:
        """Decide si continuar procesando o detenerse a esperar al agente humano."""
        respuesta_humano = state.get("respuesta_humano", "")
        if respuesta_humano:
            return "procesar_humano"
        else:
            return "esperar"

    # --------------------------------------------------------------------------
    # PASO 6: CONSTRUCCIÓN Y ESTRUCTURA DEL GRAFO
    # --------------------------------------------------------------------------
    def crear_grafo(self):
        """Crea la estructura de nodos y aristas del StateGraph de LangGraph."""
        graph = StateGraph(HelpdeskState)

        # 1. Registrar nodos
        graph.add_node("rag", self.procesar_rag)
        graph.add_node("clasificar", self.clasificar_con_contexto)        
        graph.add_node("escalar", self.preparar_escalado)
        graph.add_node("respuesta_final", self.generar_respuesta_final)
        graph.add_node("procesar_humano", self.procesar_respuesta_humano)

        # 2. Conexiones fijas iniciales
        graph.add_edge(START, "rag")
        graph.add_edge("rag", "clasificar")

        # 3. Eje condicional: desde clasificar hacia respuesta_final o escalar
        graph.add_conditional_edges(
            "clasificar",
            self.decidir_desde_clasificacion,
            {
                "respuesta_final": "respuesta_final",
                "escalar": "escalar"
            }
        )

        # 4. Eje condicional: desde escalar hacia procesar_humano o pausa (END)
        graph.add_conditional_edges(
            "escalar",
            self.decidir_desde_humano,
            {
                "procesar_humano": "procesar_humano",
                "esperar": END
            }
        )      
        
        # 5. Conexiones a finalización (END)
        graph.add_edge("procesar_humano", END)
        graph.add_edge("respuesta_final", END)

        self.graph = graph
        return graph

    # --------------------------------------------------------------------------
    # PASO 7: COMPILACIÓN Y PERSISTENCIA (CHECKPOINTING)
    # --------------------------------------------------------------------------
    def compilar(self):
        """Compila el grafo configurando el checkpointer para persistir el estado."""
        if not self.graph:
            self.crear_grafo()

        # Usar SqliteSaver si está disponible; de lo contrario, usar MemorySaver
        if HAS_SQLITE_SAVER:
            conn = sqlite3.connect('helpdesk.db', check_same_thread=False)
            checkpointer = SqliteSaver(conn)
        else:
            checkpointer = MemorySaver()
        
        # Compilar con interrupción para intervención humana antes del nodo procesar_humano
        compiled = self.graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["procesar_humano"]                
        )
        return compiled

# ------------------------------------------------------------------------------
# PASO 8: FUNCIÓN CONSTRUCTORA AUXILIAR
# ------------------------------------------------------------------------------
def crear_helpdesk():
    """Función de fábrica para instanciar y compilar el grafo Helpdesk."""
    helpdesk = HelpdeskGraph()
    return helpdesk.compilar()
