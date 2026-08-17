# ==============================================================================
# PROCESADOR DE REUNIONES CON LANGGRAPH Y SALIDAS ESTRUCTURADAS (STRUCTURED OUTPUT)
# ==============================================================================
# Este script procesa notas o audio/video de reuniones mediante un flujo secuencial:
# PASO 1: Definir el Estado compartido y los esquemas Pydantic.
# PASO 2: Configurar el modelo de lenguaje (LLM).
# PASO 3: Definir los Nodos de trabajo (Extracción -> Generación de entregables).
# PASO 4: Construir, conectar y compilar el Grafo de LangGraph.
# PASO 5: Funciones auxiliares de transcripción (Whisper API / MoviePy).
# PASO 6: Invocación y presentación de resultados.
# ==============================================================================

import os
from typing import TypedDict, List
from tkinter import Tk, filedialog
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Importación opcional de moviepy para extracción de audio en videos
try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False


# ------------------------------------------------------------------------------
# PASO 1: DEFINICIÓN DEL ESTADO Y ESQUEMAS DE SALIDA ESTRUCTURADA
# ------------------------------------------------------------------------------

# 1.1 Estado global de LangGraph que se actualizará paso a paso
class State(TypedDict):
    notes: str                  # Entrada: notas o transcripción completa de la reunión
    participants: List[str]     # Nombres de asistentes extraídos
    topics: List[str]           # Temas principales discutidos
    action_items: List[str]     # Tareas/compromisos acordados
    minutes: str                # Minuta formal redactada
    summary: str                # Resumen ejecutivo breve

# 1.2 Esquema Pydantic para la extracción estructurada de datos iniciales
class MeetingAnalysis(BaseModel):
    participants: List[str] = Field(description="Nombres de las personas que asistieron o hablaron en la reunión.")
    topics: List[str] = Field(description="Los 3 a 5 temas principales discutidos en la reunión.")
    action_items: List[str] = Field(description="Acciones específicas acordadas y responsables, o tareas pendientes.")

# 1.3 Esquema Pydantic para la generación estructurada de los entregables finales
class MeetingDeliverables(BaseModel):
    minutes: str = Field(description="Minuta formal, estructurada y profesional (máximo 150 palabras).")
    summary: str = Field(description="Resumen ejecutivo ultra-breve de máximo 2 líneas (30 palabras).")


# ------------------------------------------------------------------------------
# PASO 2: CONFIGURACIÓN DEL MODELO DE LENGUAJE (LLM)
# ------------------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


# ------------------------------------------------------------------------------
# PASO 3: DEFINICIÓN DE LOS NODOS DEL WORKFLOW
# Cada nodo recibe el Estado actual y retorna un diccionario con las actualizaciones.
# ------------------------------------------------------------------------------

def extract_meeting_data(state: State) -> dict:
    """NODO 1: Extrae participantes, temas clave y compromisos usando Structured Output."""
    print("🔍 [NODO 1] Analizando notas y extrayendo datos estructurados...")
    
    prompt = f"""
    Analiza las siguientes notas de reunión y extrae de forma estructurada:
    1. Los nombres de los participantes.
    2. Los 3-5 temas principales discutidos.
    3. Las acciones, compromisos o tareas acordadas con responsables.
    
    Notas de reunión:
    {state['notes']}
    """
    
    structured_llm = llm.with_structured_output(MeetingAnalysis)
    try:
        response = structured_llm.invoke(prompt)
        print(f"  ✓ Datos extraídos: {len(response.participants)} participantes, {len(response.topics)} temas, {len(response.action_items)} acciones.")
        return {
            'participants': response.participants,
            'topics': response.topics,
            'action_items': response.action_items
        }
    except Exception as e:
        print(f"  ❌ Error en extracción estructurada: {e}")
        return {'participants': [], 'topics': [], 'action_items': []}


def generate_deliverables(state: State) -> dict:
    """NODO 2: Genera la minuta formal y el resumen ejecutivo a partir de los datos procesados."""
    print("✍️ [NODO 2] Generando entregables (minuta y resumen ejecutivo)...")
    
    participants_str = ", ".join(state['participants']) if state['participants'] else "No especificados"
    topics_str = "\n• ".join(state['topics']) if state['topics'] else "No especificados"
    actions_str = "\n• ".join(state['action_items']) if state['action_items'] else "No se definieron acciones específicas"
    
    prompt = f"""
    Basándote en la información estructurada procesada de la reunión, genera los entregables:
    1. Una minuta formal y profesional (máximo 150 palabras).
    2. Un resumen ejecutivo ultra-breve (máximo 2 líneas, 30 palabras).
    
    Información procesada:
    - PARTICIPANTES: {participants_str}
    - TEMAS TRATADOS:
      • {topics_str}
    - ACCIONES ACORDADAS:
      • {actions_str}
      
    Notas originales como contexto:
    {state['notes']}
    """
    
    structured_llm = llm.with_structured_output(MeetingDeliverables)
    try:
        response = structured_llm.invoke(prompt)
        print("  ✓ Entregables redactados con éxito.")
        return {
            'minutes': response.minutes,
            'summary': response.summary
        }
    except Exception as e:
        print(f"  ❌ Error redactando entregables: {e}")
        return {
            'minutes': "Error al generar la minuta formal.",
            'summary': "Error al generar el resumen ejecutivo."
        }


# ------------------------------------------------------------------------------
# PASO 4: CONSTRUCCIÓN, REGISTRO Y COMPILACIÓN DEL GRAFO
# ------------------------------------------------------------------------------
def create_workflow():
    """Crea, conecta los nodos en secuencia y compila el flujo de trabajo."""
    workflow = StateGraph(State)
    
    # 4.1 Registrar los nodos en el grafo
    workflow.add_node("extract_meeting_data", extract_meeting_data)
    workflow.add_node("generate_deliverables", generate_deliverables)
    
    # 4.2 Conectar el flujo secuencial con aristas (edges)
    workflow.add_edge(START, "extract_meeting_data")
    workflow.add_edge("extract_meeting_data", "generate_deliverables")
    workflow.add_edge("generate_deliverables", END)
    
    # 4.3 Compilar el grafo en un Runnable ejecutable
    return workflow.compile()


# ------------------------------------------------------------------------------
# PASO 5: FUNCIONES AUXILIARES DE PROCESAMIENTO Y TRANSCRIPCIÓN
# ------------------------------------------------------------------------------

def extract_audio_from_video(video_path: str) -> str:
    """Extrae la pista de audio de un archivo de video y genera un mp3 temporal."""
    if not HAS_MOVIEPY:
        print("  ⚠️ MoviePy no disponible. Intentando procesar video directo...")
        return video_path
        
    try:
        print("  🎬 Extrayendo audio del archivo de video...")
        video = VideoFileClip(video_path)
        temp_audio_path = os.path.splitext(video_path)[0] + "_temp.mp3"
        video.audio.write_audiofile(temp_audio_path, logger=None)
        video.close()
        print(f"  ✓ Audio temporal generado: {temp_audio_path}")
        return temp_audio_path
    except Exception as e:
        print(f"  ⚠️ Error extrayendo audio: {e}")
        return video_path


def transcribe_media_direct(file_path: str) -> str:
    """Transcribe archivos de audio/video utilizando OpenAI Whisper API."""
    temp_audio_path = None
    try:
        print("🎙️ Transcribiendo con OpenAI Whisper API...")
        video_exts = {".mp4", ".mov", ".mkv", ".webm"}
        ext = os.path.splitext(file_path)[1].lower()
        
        target_path = file_path
        if ext in video_exts:
            temp_audio_path = extract_audio_from_video(file_path)
            target_path = temp_audio_path
            
        client = OpenAI()
        file_size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"  📂 Archivo: {os.path.basename(target_path)} ({file_size_mb:.2f} MB)")
        
        if file_size_mb > 25:
            raise ValueError(f"El archivo supera el límite de 25 MB de Whisper ({file_size_mb:.2f} MB).")
            
        with open(target_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",
                prompt="Reunión de trabajo en español.",
                response_format="text"
            )
        
        print(f"  ✓ Transcripción finalizada ({len(transcript)} caracteres).")
        return transcript
        
    except Exception as e:
        print(f"  ❌ Error de transcripción: {e}")
        return f"Error en la transcripción: {str(e)}"
    finally:
        if temp_audio_path and temp_audio_path != file_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print(f"  🧹 Archivo temporal eliminado: {temp_audio_path}")
            except Exception:
                pass


def display_results(result: State, meeting_num: int):
    """Muestra en consola el resultado final del flujo de LangGraph de forma legible."""
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
    print("\n" + "="*60)


# ------------------------------------------------------------------------------
# PASO 6: INVOCACIÓN Y EJECUCIÓN PRINCIPAL
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Compilar el flujo de LangGraph
    app = create_workflow()

    # Abrir selector de archivos mediante GUI
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Selecciona un archivo de audio, video o texto",
        filetypes=[
            ("Vídeo/Audio", "*.mp4 *.mov *.m4a *.mp3 *.wav *.mkv *.webm"),
            ("Texto", "*.txt *.md")
        ]
    )

    if not file_path:
        print("No se seleccionó ningún archivo.")
        raise SystemExit(0)

    # Leer texto o transcribir según el formato
    ext = os.path.splitext(file_path)[1].lower()
    media_exts = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".mkv", ".webm"}

    if ext in media_exts:
        notes = transcribe_media_direct(file_path) 
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            notes = f.read()

    if notes.startswith("Error en la transcripción:"):
        print("🛑 Deteniendo flujo por error en la transcripción.")
        raise SystemExit(1)

    # Inicializar el Estado e invocar el grafo
    initial_state = {
        'notes': notes,
        'participants': [],
        'topics': [],
        'action_items': [],
        'minutes': '',
        'summary': ''
    }
    
    print("\n🚀 Iniciando ejecución del grafo de LangGraph...")
    result = app.invoke(initial_state)
    display_results(result, 1)