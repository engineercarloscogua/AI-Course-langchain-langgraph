# ==============================================================================
# USO DE ANNOTATED Y REDUCERS (OPERATOR.ADD) EN EL ESTADO DE LANGGRAPH
# ==============================================================================
# Este archivo enseña cómo acumular datos a lo largo del flujo usando Annotated.
# En lugar de sobrescribir una clave, la función reductora (ej. operator.add)
# concatena los resultados generados por múltiples nodos independientes.
# ==============================================================================

import os
import sys
import io
from typing import TypedDict, List, Annotated
from operator import add
from tkinter import Tk, filedialog
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Cargar variables de entorno (.env)
load_dotenv()

# Ajustar codificación UTF-8 en consola de Windows si fuera necesario
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ------------------------------------------------------------------------------
# PASO 1: DEFINICIÓN DEL ESTADO CON REDUCERS (ANNOTATED)
# ------------------------------------------------------------------------------
# Al usar Annotated[List[str], add], LangGraph sabrá que cuando un nodo
# devuelva 'logs', no debe reemplazar la lista existente, sino concatenar (add)
# los nuevos elementos a la lista acumulada.
# ------------------------------------------------------------------------------
class State(TypedDict):
    notes: str                  # Texto original o transcripción
    participants: List[str]     # Lista de participantes extraídos
    topics: List[str]           # Lista de temas principales
    action_items: List[str]     # Lista de acciones acordadas
    minutes: str                # Minuta formal generada
    summary: str                # Resumen ejecutivo breve
    logs: Annotated[List[str], add]  # ACUMULADOR: Concatena entradas de log con operator.add


# ------------------------------------------------------------------------------
# PASO 2: CONFIGURACIÓN DEL MODELO DE LENGUAJE (LLM)
# ------------------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


# ------------------------------------------------------------------------------
# PASO 3: DEFINICIÓN DE LOS NODOS DEL WORKFLOW
# Cada nodo actualiza sus claves correspondientes y añade una entrada al log acumulado.
# ------------------------------------------------------------------------------

def extract_participants(state: State) -> dict:
    """NODO 1: Extrae participantes de la reunión."""
    prompt = f"""
    De las siguientes notas de reunión, extrae SOLO los nombres de los participantes.
    Notas: {state['notes']}
    Responde ÚNICAMENTE con una lista de nombres separados por comas, sin explicaciones.
    Ejemplo: Juan García, María López, Carlos Ruiz
    """
    response = llm.invoke(prompt)
    participants = [p.strip() for p in response.content.split(',') if p.strip()]
    print(f"✓ [NODO 1] Participantes extraídos: {len(participants)} personas")
    
    return {
        'participants': participants,
        'logs': ["Paso 1 completado: Extracción de participantes"]
    }


def identify_topics(state: State) -> dict:
    """NODO 2: Identifica los temas principales discutidos."""
    prompt = f"""
    Identifica los 3-5 temas principales discutidos en esta reunión.
    Notas: {state['notes']}
    Responde SOLO con los temas separados por punto y coma (;).
    Ejemplo: Arquitectura del sistema; Plazos de entrega; Asignación de tareas
    """
    response = llm.invoke(prompt)
    topics = [t.strip() for t in response.content.split(';') if t.strip()]
    print(f"✓ [NODO 2] Temas identificados: {len(topics)} temas")
    
    return {
        'topics': topics,
        'logs': ["Paso 2 completado: Identificación de temas"]
    }


def extract_actions(state: State) -> dict:
    """NODO 3: Extrae las tareas acordadas y sus responsables."""
    prompt = f"""
    Extrae las acciones específicas acordadas en la reunión con su responsable.
    Notas: {state['notes']}
    Formato de respuesta: Una acción por línea, separadas por |
    Ejemplo: María se encargará del backend | Carlos preparará el plan de testing
    Si no hay acciones claras, responde con: "No se identificaron acciones específicas"
    """
    response = llm.invoke(prompt)
    
    if "No se identificaron" in response.content:
        action_items = []
    else:
        action_items = [a.strip() for a in response.content.split('|') if a.strip()]
    
    print(f"✓ [NODO 3] Acciones extraídas: {len(action_items)} items")
    
    return {
        'action_items': action_items,
        'logs': ["Paso 3 completado: Extracción de acciones"]
    }


def generate_minutes(state: State) -> dict:
    """NODO 4: Genera una minuta formal redactada."""
    participants_str = ", ".join(state['participants']) if state['participants'] else "No especificados"
    topics_str = "\n• ".join(state['topics']) if state['topics'] else "No especificados"
    actions_str = "\n• ".join(state['action_items']) if state['action_items'] else "Sin acciones especificadas"
    
    prompt = f"""
    Genera una minuta formal y profesional (máximo 150 palabras):
    PARTICIPANTES: {participants_str}
    TEMAS DISCUTIDOS:
    • {topics_str}
    ACCIONES ACORDADAS:
    • {actions_str}
    NOTAS ORIGINALES: {state['notes']}
    """
    response = llm.invoke(prompt)
    print(f"✓ [NODO 4] Minuta formal generada.")
    
    return {
        'minutes': response.content,
        'logs': ["Paso 4 completado: Redacción de minuta formal"]
    }


def create_summary(state: State) -> dict:
    """NODO 5: Crea un resumen ejecutivo breve."""
    prompt = f"""
    Crea un resumen ejecutivo de MÁXIMO 2 líneas (30 palabras) que capture la esencia de la reunión.
    Participantes: {', '.join(state['participants'][:3])}
    Tema principal: {state['topics'][0] if state['topics'] else 'General'}
    Acciones clave: {len(state['action_items'])} acciones definidas
    """
    response = llm.invoke(prompt)
    print(f"✓ [NODO 5] Resumen ejecutivo creado.")
    
    return {
        'summary': response.content,
        'logs': ["Paso 5 completado: Creación de resumen ejecutivo"]
    }


# ------------------------------------------------------------------------------
# PASO 4: CONSTRUCCIÓN, REGISTRO Y COMPILACIÓN DEL GRAFO
# ------------------------------------------------------------------------------
def create_workflow():
    """Crea, registra los nodos y conecta el flujo en secuencia lineal."""
    workflow = StateGraph(State)
    
    # 4.1 Registrar nodos
    workflow.add_node("extract_participants", extract_participants)
    workflow.add_node("identify_topics", identify_topics)
    workflow.add_node("extract_actions", extract_actions)
    workflow.add_node("generate_minutes", generate_minutes)
    workflow.add_node("create_summary", create_summary)
    
    # 4.2 Conectar flujo secuencial
    workflow.add_edge(START, "extract_participants")
    workflow.add_edge("extract_participants", "identify_topics")
    workflow.add_edge("identify_topics", "extract_actions")
    workflow.add_edge("extract_actions", "generate_minutes")
    workflow.add_edge("generate_minutes", "create_summary")
    workflow.add_edge("create_summary", END)
    
    # 4.3 Compilar el grafo
    return workflow.compile()


# ------------------------------------------------------------------------------
# PASO 5: FUNCIONES AUXILIARES DE PROCESAMIENTO Y TRANSCRIPCIÓN
# ------------------------------------------------------------------------------

def transcribe_media_direct(file_path: str) -> str:
    """Transcribe archivos de audio usando directamente OpenAI Whisper API."""
    try:
        print("🎙️ Transcribiendo audio con OpenAI Whisper...")
        client = OpenAI()
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",
                prompt="Reunión de trabajo en español.",
                response_format="text"
            )
        print(f"  ✓ Transcripción lista ({len(transcript)} caracteres).")
        return transcript
    except Exception as e:
        print(f"  ❌ Error en transcripción: {e}")
        return f"Error: {str(e)}"


def display_results(result: State, meeting_num: int):
    """Muestra la salida formateada del estado y la lista acumulada de logs."""
    print(f"\n📋 RESULTADOS FINALES DEL GRAFO - REUNIÓN #{meeting_num}")
    print("="*60)
    
    print(f"\n👥 Participantes ({len(result['participants'])}):")
    for p in result['participants']:
        print(f"   • {p}")
    
    print(f"\n📍 Temas tratados ({len(result['topics'])}):")
    for t in result['topics']:
        print(f"   • {t}")
    
    print(f"\n✅ Acciones acordadas ({len(result['action_items'])}):")
    if result['action_items']:
        for a in result['action_items']:
            print(f"   • {a}")
    else:
        print("   • No se definieron acciones específicas")
    
    print(f"\n📄 MINUTA FORMAL:")
    print("-"*40)
    print(result['minutes'])
    print("-"*40)
    
    print(f"\n💡 RESUMEN EJECUTIVO:")
    print(f"   {result['summary']}")
    
    print("\n📜 HISTORIAL ACUMULADO DE LOGS (GRACIAS A ANNOTATED & OPERATOR.ADD):")
    print("-"*60)
    for log_entry in result['logs']:
        print(f"   🔹 {log_entry}")
    print("="*60)


# ------------------------------------------------------------------------------
# PASO 6: INVOCACIÓN Y EJECUCIÓN PRINCIPAL
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_workflow()

    file_path = None
    if len(sys.argv) > 1 and sys.argv[1] != "--demo":
        file_path = sys.argv[1]
    elif len(sys.argv) == 1 and not os.environ.get("NO_GUI"):
        try:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="Selecciona un archivo de audio o texto",
                filetypes=[
                    ("Vídeo/Audio", "*.mp4 *.mov *.m4a *.mp3 *.wav *.mkv *.webm"),
                    ("Texto", "*.txt *.md")
                ]
            )
            root.destroy()
        except Exception:
            file_path = None

    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        media_exts = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".mkv", ".webm"}

        if ext in media_exts:
            notes = transcribe_media_direct(file_path) 
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                notes = f.read()
    else:
        print("ℹ️ Usando notas de demostración por defecto...")
        notes = """
        Reunión de planificación del proyecto Alfa.
        Asistentes: Juan García, María López, Carlos Ruiz.
        Temas discutidos:
        1. Arquitectura del sistema y migración a microservicios.
        2. Plazos de entrega para la fase 1.
        3. Asignación de tareas de pruebas y backend.
        Acciones acordadas:
        - María se encargará del backend y la API REST.
        - Carlos preparará el plan de testing y las pruebas unitarias.
        - Próxima reunión el próximo lunes a las 10:00 AM.
        """

    initial_state = {
        'notes': notes,
        'participants': [],
        'topics': [],
        'action_items': [],
        'minutes': '',
        'summary': '',
        'logs': []
    }
    
    print("\n🚀 Ejecutando grafo con reductor de logs...")
    result = app.invoke(initial_state)
    display_results(result, 1)