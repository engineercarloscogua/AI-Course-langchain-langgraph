"""Grafo conversacional con varios usuarios y varios chats por usuario.

Flujo de cada turno:

1. Recuperar memorias transversales relevantes desde Chroma.
2. Recortar una copia del historial que se enviará al modelo.
3. Generar la respuesta y agregarla al historial completo.
4. Extraer del mensaje del usuario una posible memoria transversal.

SQLite conserva por separado el estado de cada ``thread_id``. Chroma, en
cambio, se comparte entre todos los chats pertenecientes al mismo usuario.

Aunque utiliza componentes habituales en sistemas de agentes, este ejercicio
es un *workflow* determinista, no un agente autónomo: el orden de los cuatro
nodos está fijado y el modelo no elige herramientas ni decide qué nodo ejecutar.
"""

# Biblioteca estándar:
# - sqlite3 abre el archivo donde LangGraph guarda checkpoints;
# - datetime genera timestamps independientes de la zona horaria local.
import sqlite3
from datetime import datetime, timezone

# Tipos de mensaje y utilidades de contexto de LangChain.
# HumanMessage y AIMessage permiten distinguir quién escribió cada entrada.
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages

# ChatPromptTemplate compone mensajes de sistema + historial. El placeholder
# marca el lugar donde se insertará la lista de mensajes de la conversación.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# SqliteSaver implementa la persistencia de estado; StateGraph define los nodos
# y START/END representan los límites del recorrido.
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_CONTEXT_TOKENS
from memory_manager import MemoryState, ModernMemoryManager


def _utc_now() -> str:
    """Devuelve una fecha UTC serializable dentro de un mensaje."""

    # Los mensajes de LangChain no añaden por sí solos una fecha de creación.
    # La guardamos en additional_kwargs para que una futura UI pueda mostrarla.
    return datetime.now(timezone.utc).isoformat()


# 1. Crea un chatbot independiente para un usuario.
class ModernChatbot:
    """Coordina el LLM, LangGraph y las dos clases de memoria.

    Crear este objeto prepara recursos; llamar ``chat`` ejecuta un turno.
    """

    def __init__(self, user_id: str):
        # 1.1. El gestor valida el ID, crea su carpeta, abre Chroma y prepara la
        # cadena que extraerá recuerdos. Se conserva como dependencia del grafo.
        self.memory_manager = ModernMemoryManager(user_id)

        # Se usa el ID normalizado del gestor (por ejemplo, sin espacios laterales).
        self.user_id = self.memory_manager.user_id

        # 1.2. Esta es la instancia del modelo usada para responder. Construirla
        # no envía mensajes; la llamada real ocurre en response_generation_node.
        self.llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
        )

        # 1.3. Este mensaje de sistema define el comportamiento estable.
        # ``{context}`` no es una variable que OpenAI resuelva: Python la reemplaza en
        # cada turno con memorias recuperadas de Chroma antes de llamar al modelo.
        self.system_template = """Eres un asistente personal inteligente y amigable.

Características de tu personalidad:
- Eres útil, empático y conversacional.
- Recuerdas información importante de conversaciones anteriores.
- Adaptas tu estilo a las preferencias del usuario.
- Eres proactivo ofreciendo sugerencias relevantes.
- Mantienes un tono profesional pero cercano.

{context}

Usa esta información para personalizar tus respuestas. No menciones explícitamente que tienes memoria, salvo que sea relevante para la conversación."""

        # 1.4. Construye y compila el grafo una sola vez por objeto. Después,
        # ``self.app`` ofrece invoke, get_state y otras operaciones de LangGraph.
        self.app = self._create_app()

    # 2. Define los cuatro nodos y su orden de ejecución.
    def _create_app(self):
        """Define, conecta y compila la máquina de estados conversacional.

        Un nodo recibe el estado actual y devuelve solo las claves que desea
        actualizar. LangGraph combina ese resultado con el estado antes de pasar
        al siguiente nodo.
        """

        # 2.1. MemoryState declara qué claves pueden viajar entre nodos y qué
        # reducer se debe aplicar a ``messages``.
        workflow = StateGraph(MemoryState)

        # Nodo 1/4: consulta la memoria de largo plazo con el mensaje reciente.
        def memory_retrieval_node(state: MemoryState) -> dict:
            """Busca en Chroma usando como consulta el último mensaje humano."""

            # 2.2. ``get`` retorna [] si este fuera un estado inicial sin mensajes.
            messages = state.get("messages", [])

            # 2.3. Se recorre al revés porque el mensaje relevante normalmente es
            # el último. ``next(..., None)`` se detiene en el primer HumanMessage y
            # evita recorrer todo el historial si ya lo encontró.
            last_user_message = next(
                (
                    message
                    for message in reversed(messages)
                    if isinstance(message, HumanMessage)
                ),
                None,
            )

            # Un grafo invocado sin mensaje humano no tiene consulta semántica.
            if last_user_message is None:
                return {"vector_memories": []}

            # 2.4. Chroma vectoriza el texto y recupera los recuerdos más próximos.
            # ``content`` puede admitir otros formatos en LangChain; este ejercicio
            # lo convierte a str porque trabaja con mensajes de texto.
            memories = self.memory_manager.search_vector_memory(
                str(last_user_message.content)
            )

            # El nodo devuelve una actualización parcial. No tiene que devolver
            # ``messages`` porque LangGraph conserva las otras claves del estado.
            return {"vector_memories": memories}

        # Nodo 2/4: recorta solo la copia que verá el LLM. El historial completo
        # permanece en ``messages`` y SQLite puede seguir mostrándolo en la UI.
        def context_optimization_node(state: MemoryState) -> dict:
            """Prepara una ventana válida del historial para la próxima llamada."""

            # 2.5. trim_messages no resume ni modifica el texto: selecciona qué
            # mensajes completos caben dentro del presupuesto aproximado.
            context_messages = trim_messages(
                state.get("messages", []),

                # strategy="last": conserva la parte más reciente del chat.
                strategy="last",

                # Presupuesto de entrada dedicado al historial. El prompt de
                # sistema y la salida del modelo consumen tokens adicionales.
                max_tokens=MAX_CONTEXT_TOKENS,

                # Conteo local aproximado: es rápido y no llama a OpenAI.
                token_counter=count_tokens_approximately,

                # Si se corta el inicio, procura que la ventana comience con un
                # turno humano y no con una respuesta aislada del asistente.
                start_on="human",

                # Antes de generar una respuesta, la ventana debe terminar en el
                # mensaje humano actual (o en un ToolMessage en grafos con tools).
                end_on=("human", "tool"),
            )

            # Se guarda en otra clave. Si se retornara bajo ``messages``, el
            # reducer add_messages fusionaría listas y no conseguiría recortarla.
            return {"context_messages": context_messages}

        # Nodo 3/4: compone el prompt, llama a OpenAI y agrega la respuesta.
        def response_generation_node(state: MemoryState) -> dict:
            """Combina personalidad, recuerdos e historial para llamar al LLM."""

            # 2.6. Normalmente usa la ventana del nodo 2. El segundo argumento de
            # get es un fallback útil si este nodo se reutilizara sin pasar por él.
            messages = state.get("context_messages", state.get("messages", []))
            if not messages:
                # Sin conversación no hay nada que responder ni que agregar.
                return {}

            # 2.7. Obtiene los recuerdos encontrados por el nodo 1. Esta lista se
            # reemplaza en cada turno, no es todo lo almacenado en Chroma.
            memories = state.get("vector_memories", [])
            if memories:
                # Convierte ["dato 1", "dato 2"] en viñetas legibles para el LLM.
                memory_lines = "\n".join(f"- {memory}" for memory in memories)
                context = (
                    "Información relevante que recuerdas del usuario:\n"
                    f"{memory_lines}"
                )
            else:
                # El prompt siempre recibe un valor para {context}, incluso cuando
                # el usuario aún no tiene recuerdos transversales.
                context = "No hay información previa relevante disponible."

            # 2.8. El prompt final tiene dos piezas:
            # a) SystemMessage: personalidad + memoria transversal recuperada;
            # b) MessagesPlaceholder: ventana de HumanMessage/AIMessage.
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system_template.format(context=context)),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

            # 2.9. LCEL pasa el prompt formateado a ChatOpenAI. Aquí sí ocurre la
            # llamada de red y ``response`` es una AIMessage.
            response = (prompt | self.llm).invoke({"messages": messages})

            # 2.10. Añade un dato auxiliar que SQLite serializará junto al mensaje.
            response.additional_kwargs["timestamp"] = _utc_now()

            # Se retorna una lista porque ``messages`` usa add_messages. El reducer
            # agrega esta respuesta al historial completo en lugar de reemplazarlo.
            return {"messages": [response]}

        # Nodo 4/4: guarda, como máximo, una memoria del último mensaje humano.
        def memory_extraction_node(state: MemoryState) -> dict:
            """Analiza el último mensaje humano después de generar la respuesta."""

            # 2.11. En este punto messages ya incluye la AIMessage del nodo 3.
            messages = state.get("messages", [])

            # Por eso se busca explícitamente el HumanMessage más reciente y no
            # se toma simplemente messages[-1], que sería la respuesta del bot.
            last_user_message = next(
                (
                    message
                    for message in reversed(messages)
                    if isinstance(message, HumanMessage)
                ),
                None,
            )
            if last_user_message is None:
                return {}

            # 2.12. LangGraph asigna ID a los mensajes agregados. Usar ese ID evita
            # omitir dos turnos distintos que por casualidad tengan igual texto.
            # El contenido queda como fallback para mensajes antiguos sin ID.
            extraction_id = last_user_message.id or str(last_user_message.content)

            # Si se reanuda el mismo checkpoint, no repetimos una llamada costosa
            # ni guardamos una copia idéntica del recuerdo.
            if state.get("last_memory_extraction") == extraction_id:
                return {}

            # 2.13. El manager decidirá mediante LLM (o reglas manuales) si existe
            # un hecho suficientemente importante y lo insertará en Chroma.
            self.memory_manager.extract_and_store_memory(
                str(last_user_message.content)
            )

            # Se persiste el marcador aunque el mensaje no produjera memoria: ya
            # fue analizado y no tiene sentido volver a pagar por analizarlo.
            return {"last_memory_extraction": extraction_id}

        # 2.14. Registrar un nodo asocia un nombre interno con su función Python.
        # Los nombres aparecen también en trazas y ayudan a depurar el recorrido.
        workflow.add_node("memory_retrieval", memory_retrieval_node)
        workflow.add_node("context_optimization", context_optimization_node)
        workflow.add_node("response_generation", response_generation_node)
        workflow.add_node("memory_extraction", memory_extraction_node)

        # 2.15. Las aristas determinan el orden. No hay decisiones condicionales
        # en este ejercicio: todos los turnos recorren los cuatro nodos.
        workflow.add_edge(START, "memory_retrieval")
        workflow.add_edge("memory_retrieval", "context_optimization")
        workflow.add_edge("context_optimization", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", END)

        # 3. Configura la persistencia de la memoria de corto plazo.
        #
        # 3.1. sqlite3 abre (o crea) el archivo privado del usuario. La conexión
        # vive tanto como este objeto y se cierra explícitamente en ``close``.
        self._db_connection = sqlite3.connect(
            self.memory_manager.langgraph_db_path,

            # Streamlit u otra futura UI puede atender interacciones desde hilos
            # distintos. SqliteSaver incorpora un lock; esta opción permite usar
            # la conexión desde esos hilos sin que sqlite3 la rechace primero.
            check_same_thread=False,
        )

        # 3.2. SqliteSaver traduce el protocolo de checkpoints de LangGraph a
        # tablas y operaciones SQLite. No genera respuestas ni embeddings.
        self._checkpointer = SqliteSaver(self._db_connection)

        # 3.3. compile valida el grafo y conecta el checkpointer. Desde ahora,
        # antes de cada invoke se recupera el thread y tras cada paso se guarda.
        return workflow.compile(checkpointer=self._checkpointer)

    def _thread_id(self, chat_id: str) -> str:
        """Combina usuario y chat para crear la clave usada por SqliteSaver.

        Ejemplo: usuario ``ana`` + chat ``abc`` -> ``user_ana_chat_abc``.
        """

        # 3.4. Un mismo usuario puede mantener varios historiales porque cambia
        # chat_id. Dos usuarios tampoco colisionan aunque reutilicen el mismo ID.
        return f"user_{self.user_id}_chat_{chat_id}"

    # 4. Ejecuta un turno completo del grafo.
    def chat(self, message: str, chat_id: str = "default") -> dict:
        """Ejecuta un turno y devuelve un diccionario estable para la futura UI.

        La función no lanza hacia la interfaz los errores normales de API o BD:
        los convierte en ``success=False`` y conserva el detalle en ``error``.
        """

        # 4.1. Validación previa: strip permite detectar "   " como vacío. Se
        # retorna antes de crear títulos, embeddings o llamadas al LLM.
        if not message.strip():
            return {
                "success": False,
                "response": None,
                "error": "El mensaje no puede estar vacío.",
                "memories_used": 0,
                "context_optimized": False,
            }

        try:
            # 4.2. LangGraph espera thread_id dentro de configurable, no al mismo
            # nivel que messages. Repetirlo continúa el chat; cambiarlo lo aísla.
            # la conversación aunque el usuario sea el mismo.
            config = {
                "configurable": {"thread_id": self._thread_id(chat_id)}
            }

            # 4.3. Los metadatos JSON y el historial SQLite son mecanismos
            # separados. Aquí se asegura que la futura lista lateral tenga título.
            chat_info = self.memory_manager.get_chat_info(chat_id)

            # Si el chat no estaba en JSON o aún conserva el marcador inicial, se
            # genera el título una sola vez con el primer mensaje útil.
            if chat_info is None or chat_info.get("title") == "Nuevo chat":
                title = self.memory_manager._generate_chat_title(message)
                self.memory_manager.update_chat_metadata(chat_id, title=title)

            # 4.4. Convierte el string de la UI a un objeto HumanMessage. Los
            # tipos de mensaje permiten al modelo y al historial reconocer roles.
            user_message = HumanMessage(
                content=message,

                # additional_kwargs admite metadatos que no forman parte del texto
                # visible. LangGraph los guardará dentro del checkpoint.
                additional_kwargs={"timestamp": _utc_now()},
            )

            # 4.5. Solo se entrega el mensaje NUEVO:
            # a) SqliteSaver carga el estado anterior del thread_id;
            # b) add_messages incorpora user_message a ese estado;
            # c) se ejecutan los nodos 1, 2, 3 y 4;
            # d) SqliteSaver persiste los estados actualizados.
            result = self.app.invoke({"messages": [user_message]}, config)

            # 4.6. La última entrada ya es la AIMessage añadida por el nodo 3.
            assistant_response = result["messages"][-1].content

            # El contador solo aumenta después de completar el grafo. Un error de
            # API no se contabiliza como turno procesado correctamente.
            self.memory_manager.update_chat_metadata(
                chat_id,
                increment_messages=True,
            )

            # 4.7. La UI no necesita conocer objetos internos de LangChain: recibe
            # texto, estado de éxito y datos auxiliares sencillos.
            return {
                "success": True,
                "response": assistant_response,
                "error": None,
                "memories_used": len(result.get("vector_memories", [])),
                "context_optimized": True,
            }
        except Exception as error:
            # 4.8. Puede capturar fallos del LLM, embeddings, SQLite o del parser.
            # Convertir el error a texto permite mostrarlo sin romper la sesión.
            return {
                "success": False,
                "response": None,
                "error": str(error),
                "memories_used": 0,
                "context_optimized": False,
            }

    # 5. Lee el estado ya persistido sin ejecutar nodos ni consumir API.
    def get_conversation_history(
        self,
        chat_id: str = "default",
        limit: int = 50,
    ) -> list[dict]:
        """Lee un thread sin ejecutar el grafo y prepara mensajes para la UI."""

        # 5.1. Un límite no positivo significa que no se solicitó ningún mensaje.
        if limit <= 0:
            return []

        try:
            # 5.2. Debe reconstruirse exactamente la misma clave usada en chat().
            config = {
                "configurable": {"thread_id": self._thread_id(chat_id)}
            }

            # 5.3. get_state consulta el último checkpoint. No recorre nodos, no
            # llama al LLM, no crea embeddings y por tanto no consume API.
            state = self.app.get_state(config)

            # Un thread inexistente produce un estado sin values útiles.
            messages = state.values.get("messages", []) if state.values else []

            # 5.4. Primero se limita a los últimos N elementos. Después se filtran
            # los tipos que la UI conoce; otros futuros mensajes (por ejemplo,
            # ToolMessage) no se etiquetarían erróneamente como assistant.
            return [
                {
                    # isinstance traduce clases de LangChain a roles de interfaz.
                    "role": "user" if isinstance(message, HumanMessage) else "assistant",
                    "content": message.content,

                    # get retorna None si se trata de un checkpoint antiguo que no
                    # tenía timestamp; así se evita KeyError.
                    "timestamp": message.additional_kwargs.get("timestamp"),
                }
                for message in messages[-limit:]
                if isinstance(message, (HumanMessage, AIMessage))
            ]
        except Exception as error:
            print(f"Error obteniendo el historial: {error}")
            return []

    # 6. Borra todos los checkpoints de un chat, pero conserva sus metadatos.
    def clear_conversation(self, chat_id: str = "default") -> bool:
        """Vacía la memoria corta del chat sin quitarlo de la lista de chats."""

        try:
            # 6.1. Invocar el grafo con messages=[] no borraría nada porque el
            # reducer add_messages agrega/actualiza, no reemplaza. delete_thread
            # elimina todos los checkpoints y escrituras del ID solicitado.
            self._checkpointer.delete_thread(self._thread_id(chat_id))
            return True
        except Exception as error:
            print(f"Error limpiando la conversación: {error}")
            return False

    # 7. Borra el thread cuando la futura interfaz elimine un chat completo.
    def delete_chat_from_langgraph(self, chat_id: str) -> bool:
        """Elimina de SQLite todos los checkpoints de un chat.

        Para una eliminación completa, la interfaz deberá llamar también a
        ``memory_manager.delete_chat(chat_id)`` para quitar su entrada del JSON.
        """

        try:
            # 7.1. delete_thread es idempotente para este uso: tras borrarlo no
            # queda historial que LangGraph pueda recuperar con ese thread_id.
            self._checkpointer.delete_thread(self._thread_id(chat_id))
            return True
        except Exception as error:
            print(f"Error eliminando el chat de LangGraph: {error}")
            return False

    def close(self) -> None:
        """Libera el archivo SQLite cuando el chatbot deja de utilizarse."""

        # 7.2. Es importante en procesos largos y en Windows, donde una conexión
        # abierta puede mantener el archivo bloqueado.
        self._db_connection.close()


# 8. Reutiliza una sola instancia de chatbot por usuario durante el proceso.
class ChatbotManager:
    """Registro en RAM de chatbots ya inicializados.

    No es la memoria conversacional. Su objetivo es reutilizar conexiones,
    modelos y grafos en vez de reconstruirlos en cada interacción de la UI.
    """

    # 8.1. Las claves son user_id y los valores son instancias ModernChatbot.
    # Este diccionario se pierde al terminar el proceso, pero los datos de SQLite
    # y Chroma permanecen en disco.
    _instances: dict[str, ModernChatbot] = {}

    @classmethod
    def get_chatbot(cls, user_id: str) -> ModernChatbot:
        """Obtiene el chatbot existente o lo crea una sola vez por proceso."""

        # 8.2. Normaliza antes de consultar el diccionario para que espacios
        # accidentales no creen dos objetos que apunten al mismo usuario.
        normalized_id = user_id.strip()

        # 8.3. La primera petición inicializa Chroma, SQLite, LLM y grafo. Las
        # peticiones siguientes recuperan exactamente el mismo objeto.
        if normalized_id not in cls._instances:
            cls._instances[normalized_id] = ModernChatbot(normalized_id)
        return cls._instances[normalized_id]

    @classmethod
    def remove_chatbot(cls, user_id: str) -> None:
        """Cierra y retira una instancia sin borrar conversaciones del disco."""

        # 8.4. pop devuelve y elimina en una sola operación. El valor por defecto
        # None evita KeyError si el usuario no tenía instancia activa.
        chatbot = cls._instances.pop(user_id.strip(), None)
        if chatbot is not None:
            chatbot.close()

    @classmethod
    def clear_all(cls) -> None:
        """Cierra todas las conexiones y vacía únicamente el registro en RAM."""

        # 8.5. Primero se cierran las conexiones SQLite de todos los usuarios.
        for chatbot in cls._instances.values():
            chatbot.close()

        # Después se eliminan las referencias. No borra archivos SQLite, JSON ni
        # colecciones Chroma: al reiniciar podrán abrirse de nuevo.
        cls._instances.clear()
