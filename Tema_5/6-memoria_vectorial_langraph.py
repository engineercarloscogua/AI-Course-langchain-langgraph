"""Ejercicio de LangGraph con memoria volátil y memoria vectorial.

Este programa combina dos memorias diferentes:

1. Memoria volátil o de corto plazo:
   LangGraph guarda en RAM los mensajes pertenecientes a cada ``thread_id``.
   Permite continuar una conversación mientras Python permanezca abierto, pero
   desaparece al cerrar el proceso.

2. Memoria vectorial o de largo plazo:
   Chroma guarda en disco algunos datos importantes del usuario. Cada texto se
   convierte en un embedding para recuperarlo posteriormente por significado,
   aunque Python se haya cerrado o se utilice otro ``thread_id``.

Orden de ejecución al iniciar el archivo:

1. Python realiza las importaciones.
2. Se crean el modelo de chat, el modelo de embeddings y Chroma.
3. Se definen las funciones. Definirlas todavía no significa ejecutarlas.
4. Se construye y compila el grafo con su memoria temporal.
5. Se abre la interfaz de terminal y se espera un mensaje.

Orden de ejecución de cada mensaje:

1. ``chat`` convierte el texto en un ``HumanMessage``.
2. ``InMemorySaver`` recupera el historial asociado al ``thread_id``.
3. LangGraph agrega el mensaje nuevo y ejecuta ``chatbot_node``.
4. El nodo busca recuerdos relacionados en Chroma.
5. El nodo une instrucciones, recuerdos e historial temporal.
6. El modelo recibe ese contexto y genera un ``AIMessage``.
7. Si el mensaje declara un dato personal, también se guarda en Chroma.
8. LangGraph añade la respuesta al historial temporal.
9. La terminal muestra el contenido de la respuesta.
"""


# GUÍA PARA QUIEN CONOCE PYTHON, PERO EMPIEZA CON ESTAS LIBRERÍAS
# ============================================================================
# OPENAI
#   Proporciona dos modelos remotos para este ejercicio:
#   - un modelo conversacional que genera respuestas;
#   - un modelo de embeddings que convierte textos en vectores.
#   Los modelos no conservan automáticamente el historial entre llamadas.
#
# LANGCHAIN
#   Proporciona integraciones para comunicarnos con OpenAI y Chroma mediante
#   objetos Python. Aquí usamos clases como ChatOpenAI, OpenAIEmbeddings,
#   HumanMessage, SystemMessage, Document y Chroma.
#
# LANGGRAPH
#   Organiza la aplicación como un flujo de trabajo. Un grafo contiene nodos
#   —funciones que realizan tareas— y aristas que indican el orden en que deben
#   ejecutarse. También administra el estado de la conversación.
#   "Grafo" aquí significa flujo de trabajo; no es una gráfica visual ni una
#   red neuronal.
#
# CHROMA
#   Es la base de datos vectorial. Guarda textos, metadatos y embeddings en
#   disco, y después busca documentos cercanos por significado.
#
# RELACIÓN ENTRE LAS HERRAMIENTAS
#   LangGraph decide CUÁNDO se ejecuta cada tarea.
#   LangChain facilita CÓMO hablar con OpenAI y Chroma.
#   OpenAI genera las respuestas y los embeddings.
#   Chroma conserva y recupera los recuerdos persistentes.
#
# VOCABULARIO IMPORTANTE
# ----------------------------------------------------------------------------
# Mensaje:
#   Objeto con un contenido y un rol. HumanMessage corresponde a la persona,
#   SystemMessage a las instrucciones y AIMessage a la respuesta del modelo.
#
# Estado:
#   Diccionario que viaja por el grafo. En este ejercicio contiene la clave
#   ``messages`` con la conversación acumulada.
#
# Nodo:
#   Función Python que recibe el estado y devuelve una actualización del estado.
#
# Arista:
#   Conexión que indica qué nodo se ejecutará después.
#
# Checkpointer:
#   Componente que toma "fotografías" del estado y permite recuperar una
#   conversación por medio de su ``thread_id``.
#
# invoke:
#   Método habitual para ejecutar componentes de LangChain o LangGraph.
#   ``llm.invoke`` ejecuta solamente el modelo, mientras que ``app.invoke``
#   ejecuta todo el grafo, incluidos sus nodos y su memoria.
#
# Embedding:
#   Lista de números que representa aproximadamente el significado de un texto.
#   No es una respuesta del asistente ni el texto cifrado.
#
# Vector store:
#   Base de datos especializada en embeddings. Chroma cumple esa función aquí.
#
# EJEMPLO DEL COMPORTAMIENTO ESPERADO
# ----------------------------------------------------------------------------
# Primera ejecución:
#   Usuario: "Me llamo Carlos"
#   - Mensaje y respuesta quedan temporalmente en InMemorySaver.
#   - "Me llamo Carlos" también queda persistentemente en Chroma.
#
# Después de cerrar y volver a abrir el archivo:
#   Usuario: "¿Cómo me llamo?"
#   - InMemorySaver comienza vacío porque se perdió la RAM anterior.
#   - Chroma recupera "Me llamo Carlos" mediante búsqueda semántica.
#   - El modelo recibe ese recuerdo y puede responder "Te llamas Carlos".


# PASO 1: IMPORTAR LAS HERRAMIENTAS NECESARIAS
# ============================================================================
# Path construye rutas válidas para Windows, macOS y Linux sin escribir barras
# manualmente. uuid4 genera un identificador irrepetible para cada recuerdo.
from pathlib import Path
from uuid import uuid4

# Document es el contenedor estándar de LangChain para datos que se guardan en
# un vector store. No representa un archivo físico:
# - page_content contiene el texto principal;
# - metadata contiene un diccionario con etiquetas descriptivas.
from langchain_core.documents import Document

# LangChain representa cada rol mediante una clase:
# - HumanMessage: texto enviado por la persona;
# - SystemMessage: instrucciones y contexto que recibe el modelo;
# - AIMessage: respuesta del modelo. No lo importamos porque llm.invoke lo crea.
from langchain_core.messages import HumanMessage, SystemMessage

# Estas clases son adaptadores de LangChain para la API de OpenAI:
# - ChatOpenAI permite ejecutar el modelo conversacional;
# - OpenAIEmbeddings permite convertir documentos y consultas en vectores.
# Ambas leen OPENAI_API_KEY desde el entorno. La clave no se escribe aquí.
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Chroma es la integración de LangChain con la base de datos vectorial. Permite
# trabajar con Document, add_documents, get y similarity_search.
from langchain_chroma import Chroma

# InMemorySaver es el checkpointer temporal de LangGraph. Guarda estados en RAM.
from langgraph.checkpoint.memory import InMemorySaver

# - MessagesState define un estado con una lista acumulable llamada messages.
# - StateGraph permite registrar los nodos y conectarlos.
# - START es el punto especial desde el cual comienza una ejecución.
from langgraph.graph import START, MessagesState, StateGraph


# PASO 2: DEFINIR LA CONFIGURACIÓN GENERAL
# ============================================================================
# __file__ es la ruta del archivo Python actual.
# resolve() la convierte en una ruta absoluta y parent obtiene su carpeta.
# El operador / agrega "chroma_memoria" a la ruta de la carpeta Tema_5.
# Así el proyecto funciona aunque se mueva a otro computador.
CHROMA_PATH = Path(__file__).resolve().parent / "chroma_memoria"

# Una colección agrupa documentos relacionados dentro de Chroma, de una forma
# parecida a una tabla. Este ejercicio utiliza una sola colección.
COLLECTION_NAME = "memoria_chat"

# IMPORTANTE: collection_name y thread_id no representan lo mismo:
# - la colección pertenece a Chroma y persiste en disco;
# - el thread_id pertenece a LangGraph y separa historiales guardados en RAM.
# Dos conversaciones no comparten historial temporal, pero sí pueden consultar
# la misma colección vectorial.

# Estas expresiones forman una regla didáctica creada por nosotros para detectar
# mensajes que posiblemente contienen datos útiles. No es una función automática
# de LangChain. En producción sería preferible una salida estructurada del LLM.
MEMORY_TRIGGERS = (
    "me llamo",
    "mi nombre es",
    "trabajo en",
    "trabajo como",
    "mi trabajo es",
    "me gusta",
    "me encanta",
    "vivo en",
    "soy de",
)


# PASO 3: CREAR EL MODELO, LOS EMBEDDINGS Y CHROMA
# ============================================================================
# El modelo genera respuestas, pero no recuerda llamadas anteriores por sí solo.
# La memoria funciona porque el programa vuelve a enviarle el contexto.
# model selecciona el modelo de OpenAI y temperature=0 reduce la aleatoriedad.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Un modelo de embeddings NO responde preguntas: convierte texto en vectores.
# Textos con significados parecidos producen vectores cercanos entre sí.
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# Usamos una única instancia de Chroma para guardar, buscar y listar recuerdos:
# - collection_name elige la colección;
# - embedding_function elige cómo convertir texto en vectores;
# - persist_directory indica dónde escribir la información en disco.
# Si la carpeta o la colección no existen, Chroma las crea automáticamente.
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=str(CHROMA_PATH),
)

# Crear estos objetos configura las integraciones, pero todavía no consulta la
# API. Las llamadas remotas ocurren al ejecutar llm.invoke, add_documents o una
# búsqueda semántica. Chroma guarda automáticamente los cambios en disco.


# PASO 4: CREAR LAS FUNCIONES DE MEMORIA VECTORIAL
# ============================================================================
# Estas funciones realizan tres tareas:
# 1. decidir si un mensaje parece contener un dato importante;
# 2. guardar el dato dentro de Chroma;
# 3. recuperar recuerdos relacionados con una consulta.
# En este punto solo se definen; se ejecutarán cuando otra parte las llame.


def es_informacion_memorizable(texto: str) -> bool:
    """Indica si el texto parece declarar un dato personal útil."""

    # 4.1: Eliminar espacios de los extremos antes de analizar el mensaje.
    texto_limpio = texto.strip()

    # 4.2: No guardar entradas vacías ni preguntas. Por ejemplo, la pregunta
    # "¿Qué color me gusta?" contiene el disparador "me gusta", pero no declara
    # un dato nuevo y, por tanto, no debe convertirse en recuerdo.
    if not texto_limpio or "?" in texto_limpio:
        return False

    # 4.3: casefold normaliza mayúsculas y minúsculas para comparar texto.
    texto_normalizado = texto_limpio.casefold()

    # 4.4: any devuelve True al encontrar el primer disparador. Si no encuentra
    # ninguno, devuelve False y el mensaje no se guarda en Chroma.
    return any(frase in texto_normalizado for frase in MEMORY_TRIGGERS)


def guardar_memoria(texto: str) -> bool:
    """Guarda el texto en Chroma si todavía no existe exactamente."""

    # La operación utiliza la API de embeddings y el disco. try/except permite
    # que un fallo vectorial no cierre completamente el chat.
    try:
        # 4.5: split y join reducen cualquier grupo de espacios a uno solo.
        texto_limpio = " ".join(texto.split())
        if not texto_limpio:
            return False

        # 4.6: get consulta los documentos existentes. include=["documents"]
        # pide solamente los textos, sin cargar sus embeddings. Chroma devuelve
        # un diccionario y or [] protege el código si la colección está vacía.
        datos_actuales = vectorstore.get(include=["documents"])
        documentos_actuales = datos_actuales.get("documents") or []

        # Comparar versiones normalizadas evita duplicados exactos que solamente
        # se diferencien por mayúsculas o minúsculas. Esta no es una búsqueda
        # semántica: únicamente comprueba igualdad textual.
        ya_existe = any(
            documento.casefold() == texto_limpio.casefold()
            for documento in documentos_actuales
        )

        # Salir aquí evita otra llamada pagada de embeddings y datos duplicados.
        if ya_existe:
            print("[=] Esa información ya estaba guardada en la memoria vectorial.")
            return False

        # 4.7: Convertir el recuerdo al formato Document de LangChain.
        # page_content guarda la frase y metadata permite clasificarla. El campo
        # tipo se utilizará después como filtro durante las búsquedas.
        recuerdo = Document(
            page_content=texto_limpio,
            metadata={"tipo": "dato_usuario"},
        )

        # 4.8: add_documents recibe listas porque también permite guardar lotes.
        # Internamente sucede lo siguiente:
        # a) OpenAIEmbeddings transforma el texto en un vector.
        # b) uuid4 crea un identificador único para el documento.
        # c) Chroma guarda ID, vector, texto y metadatos en disco.
        vectorstore.add_documents(
            documents=[recuerdo],
            ids=[str(uuid4())],
        )
        print(f"[+] Guardado en memoria vectorial: {texto_limpio}")
        return True

    except Exception as error:
        # Mostrar el detalle ayuda a detectar errores de red, API o disco.
        print(f"[!] Error guardando la memoria: {error}")
        return False


def buscar_memoria(consulta: str, k: int = 3) -> list[str]:
    """Devuelve hasta k recuerdos relacionados semánticamente con la consulta."""

    # Una búsqueda crea el embedding de la consulta mediante la API. Si falla,
    # devolvemos [] para que el chat aún pueda usar su memoria temporal.
    try:
        # 4.9: similarity_search compara el vector de la consulta con los vectores
        # guardados. k limita el resultado a un máximo de tres documentos.
        # filter revisa los metadatos y excluye otros tipos de documentos.
        documentos = vectorstore.similarity_search(
            query=consulta,
            k=k,
            filter={"tipo": "dato_usuario"},
        )

        # Chroma ordena los resultados desde el más similar. Como este ejercicio
        # no establece un puntaje mínimo, algún resultado podría ser poco relevante
        # cuando no exista una coincidencia especialmente cercana.

        # 4.10: similarity_search entrega objetos Document completos. El nodo solo
        # necesita el page_content de cada uno para construir el prompt.
        return [documento.page_content for documento in documentos]

    except Exception as error:
        print(f"[!] No fue posible consultar la memoria vectorial: {error}")
        return []


# PASO 5: DEFINIR EL NODO PRINCIPAL DEL GRAFO
# ============================================================================
# Un nodo es una función que recibe el estado y devuelve una actualización.
# Chroma y el modelo no se comunican directamente: este nodo funciona como
# puente, recupera los recuerdos y los inserta en el contexto del modelo.
#
# Entrada aproximada:
#   {"messages": [HumanMessage(...), AIMessage(...), HumanMessage(...)]}
#
# Salida aproximada:
#   {"messages": [AIMessage(...)]}


def chatbot_node(state: MessagesState) -> dict:
    """Procesa un turno completo del chat dentro del grafo."""

    # 5.1: LangGraph entrega en state todos los mensajes del thread actual.
    # [-1] selecciona el mensaje más reciente, que acaba de escribir la persona.
    messages = state["messages"]
    ultimo_mensaje = str(messages[-1].content) if messages else ""

    # 5.2: Consultar la memoria persistente. Esta búsqueda no depende del
    # thread_id; cualquier thread puede consultar la misma colección de Chroma.
    memorias = buscar_memoria(ultimo_mensaje)

    # 5.3: Crear el SystemMessage. Estas instrucciones indican cómo debe usar los
    # recuerdos y reducen el riesgo de que invente datos ausentes del contexto.
    system_content = (
        "Eres un asistente útil. Usa el historial de la conversación y los "
        "recuerdos del usuario solamente cuando sean relevantes. No inventes "
        "datos que no aparezcan en ese contexto."
    )

    # 5.4: Si Chroma encontró recuerdos, convertirlos en viñetas y agregarlos al
    # SystemMessage. Si la lista está vacía, no se añade esa sección al prompt.
    if memorias:
        recuerdos_formateados = "\n".join(
            f"- {memoria}" for memoria in memorias
        )
        system_content += (
            "\n\nRecuerdos persistentes posiblemente relacionados:\n"
            f"{recuerdos_formateados}"
        )

    # 5.5: El asterisco desempaqueta el historial dentro de una lista nueva:
    # [SystemMessage, mensaje_1, respuesta_1, mensaje_actual].
    # SystemMessage se crea de nuevo en cada turno y no se devuelve al estado;
    # por eso no se duplica dentro de la memoria temporal.
    messages_con_contexto = [SystemMessage(content=system_content), *messages]

    # 5.6: Aquí ocurre la llamada pagada al modelo conversacional.
    # llm.invoke ejecuta únicamente el modelo y devuelve un AIMessage.
    response = llm.invoke(messages_con_contexto)

    # 5.7: Guardar el mensaje original si la heurística detecta un dato útil.
    # Se guarda después de responder; el dato estará disponible desde la próxima
    # búsqueda vectorial, mientras el historial actual ya lo incluye en RAM.
    if es_informacion_memorizable(ultimo_mensaje):
        guardar_memoria(ultimo_mensaje)

    # 5.8: Devolver únicamente la respuesta nueva. MessagesState incluye una regla
    # —llamada reductor— que la agrega al historial en lugar de reemplazarlo.
    return {"messages": [response]}


# PASO 6: CONSTRUIR EL FLUJO DE LANGGRAPH
# ============================================================================
# Estas instrucciones describen el flujo; todavía no llaman al modelo.

# 6.1: Crear un grafo cuyo estado tiene la estructura de MessagesState.
workflow = StateGraph(MessagesState)

# 6.2: Registrar la función chatbot_node con el nombre interno "chatbot".
workflow.add_node("chatbot", chatbot_node)

# 6.3: Conectar START con chatbot. Como no hay otro nodo después, la ejecución
# termina cuando chatbot_node devuelve su actualización.
# Recorrido: START -> chatbot -> fin implícito.
workflow.add_edge(START, "chatbot")


# PASO 7: AGREGAR LA MEMORIA VOLÁTIL Y COMPILAR EL GRAFO
# ============================================================================
# 7.1: Crear el checkpointer temporal. Mantiene un estado por thread_id:
# - mismo thread_id: continúa el historial existente;
# - thread_id diferente: crea un historial independiente;
# - cerrar Python: todos los historiales de este objeto desaparecen.
# El checkpointer no interpreta ni resume: guarda el estado de LangGraph.
short_term_memory = InMemorySaver()

# 7.2: compile transforma la definición en una aplicación ejecutable.
# El checkpointer permite recuperar el estado antes del nodo y volver a guardarlo
# al finalizar. Chroma no se conecta aquí: se consulta dentro de chatbot_node y
# funciona como memoria persistente global, no como estado de un thread.
app = workflow.compile(checkpointer=short_term_memory)


# PASO 8: CREAR UNA FUNCIÓN PARA CONVERSAR
# ============================================================================
# message es el texto nuevo y thread_id identifica su conversación temporal.


def chat(message: str, thread_id: str = "sesion_terminal") -> str:
    """Ejecuta un turno en el thread indicado y devuelve la respuesta."""

    # 8.1: LangGraph exige que thread_id esté dentro de configurable. Esta
    # configuración controla la memoria, pero no forma parte del prompt y el
    # modelo no ve el texto "sesion_terminal".
    config = {"configurable": {"thread_id": thread_id}}

    # 8.2: Convertir el texto en HumanMessage y ejecutar el grafo completo.
    # Durante app.invoke ocurre lo siguiente:
    # a) InMemorySaver recupera el estado del thread_id.
    # b) MessagesState agrega el HumanMessage nuevo.
    # c) LangGraph recorre START -> chatbot.
    # d) chatbot_node busca recuerdos en Chroma.
    # e) chatbot_node llama al modelo y devuelve un AIMessage.
    # f) MessagesState agrega la respuesta.
    # g) InMemorySaver guarda el estado actualizado en RAM.
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # 8.3: result contiene todo el estado. El último mensaje es la respuesta
    # recién generada; extraemos content y garantizamos que sea texto.
    return str(result["messages"][-1].content)


# PASO 9: MOSTRAR LAS MEMORIAS VECTORIALES
# ============================================================================
# Esta función solo inspecciona Chroma. No ejecuta el LLM ni crea embeddings, de
# modo que el comando "memorias" no consume tokens de la API.


def mostrar_memorias() -> None:
    """Imprime los textos persistentes almacenados en Chroma."""

    try:
        # 9.1: Solicitar únicamente documents. El resultado es un diccionario
        # que también podría incluir IDs, metadatos o embeddings.
        datos = vectorstore.get(include=["documents"])
        memorias = datos.get("documents") or []

        # 9.2: Informar si la colección todavía no contiene documentos.
        if not memorias:
            print("[-] No hay información guardada en la memoria vectorial.")
            return

        # 9.3: enumerate(..., start=1) numera desde 1 para facilitar la lectura.
        print("\n[+] Memorias vectoriales guardadas:")
        for numero, memoria in enumerate(memorias, start=1):
            print(f"{numero}. {memoria}")
        print()

    except Exception as error:
        print(f"[!] Error obteniendo las memorias: {error}")


# PASO 10: ABRIR LA INTERFAZ DE TERMINAL
# ============================================================================
# Este bloque solo se ejecuta al iniciar directamente el archivo. Si otro módulo
# lo importa, __name__ no será "__main__" y la terminal no se abrirá.
if __name__ == "__main__":
    print("Chat con memoria volátil y vectorial.")
    print("Escribe 'memorias' para ver los recuerdos o 'salir' para terminar.\n")

    # 10.1: Todos los mensajes de esta ejecución comparten este thread_id.
    # Al reiniciar Python, InMemorySaver estará vacío aunque el texto del ID sea
    # igual. Chroma sí conservará sus datos porque se encuentran en disco.
    session_id = "sesion_terminal"

    # 10.2: Mantener el programa activo hasta recibir un comando de salida.
    while True:
        try:
            # 10.3: Leer el texto y eliminar espacios de sus extremos.
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            # 10.4: Ctrl+C o fin de entrada cierran el programa limpiamente.
            print("\n¡Hasta luego!")
            break

        # 10.5: Ignorar entradas vacías para no consumir la API sin necesidad.
        if not user_input:
            continue

        # Esta copia normalizada se usa solo para reconocer comandos. Conservamos
        # user_input intacto para enviarlo al modelo o guardarlo en Chroma.
        comando = user_input.casefold()

        # 10.6: Reconocer varias formas comunes de finalizar el programa.
        if comando in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        # 10.7: Mostrar Chroma sin llamar al modelo.
        if comando in {"memoria", "memorias"}:
            mostrar_memorias()
            continue

        # 10.8: Si no era un comando, procesar el turno completo y mostrarlo.
        respuesta = chat(user_input, thread_id=session_id)
        print(f"Asistente: {respuesta}\n")
