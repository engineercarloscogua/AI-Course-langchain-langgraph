"""Memoria transversal y metadatos del sistema multiusuario.

Hay dos memorias distintas en el ejercicio:

* LangGraph + SQLite conserva el historial de un chat concreto (memoria corta).
* Chroma conserva hechos de un usuario y los comparte entre sus chats
  (memoria transversal o de largo plazo).

Este archivo se ocupa de la segunda y de los metadatos ligeros de cada chat.
"""

# Biblioteca estándar:
# - json serializa la lista de chats en un archivo legible;
# - os crea rutas y directorios;
# - uuid genera identificadores que prácticamente no se repiten.
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, NotRequired, TypedDict

# Integraciones de LangChain:
# - Chroma guarda y busca documentos mediante vectores;
# - PromptTemplate introduce variables en instrucciones reutilizables;
# - PydanticOutputParser transforma texto del LLM en un objeto validado;
# - ChatOpenAI y OpenAIEmbeddings conectan con los modelos de OpenAI.
from langchain_chroma import Chroma
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from config import (
    DEFAULT_MODEL,
    EMBEDDING_MODEL,
    MAX_VECTOR_RESULTS,
    USERS_DIR,
)


def _utc_now() -> str:
    """Devuelve una fecha ISO 8601 con zona horaria UTC.

    Usar UTC evita que dos equipos en zonas horarias diferentes ordenen mal los
    chats. ``isoformat`` produce un texto apto para guardar en JSON.
    """

    # 0.1. Obtiene el instante actual con información explícita de zona horaria.
    # 0.2. Lo transforma, por ejemplo, en "2026-08-21T04:10:00+00:00".
    return datetime.now(timezone.utc).isoformat()


def _validate_user_id(user_id: str) -> str:
    """Normaliza un usuario y evita que su ID se interprete como una ruta."""

    # 0.3. Elimina espacios accidentales al principio y al final. Esto hace que
    # " ana " y "ana" representen al mismo usuario.
    normalized_id = user_id.strip()

    # 0.4. Los valores vacío, "." y ".." tienen significado especial en rutas.
    invalid_ids = {"", ".", ".."}

    # 0.5. Rechaza también separadores de carpetas. ``path.sep`` es el separador
    # principal y ``altsep`` el alternativo, cuando el sistema lo define.
    if (
        normalized_id in invalid_ids
        or os.path.sep in normalized_id
        or (os.path.altsep and os.path.altsep in normalized_id)
    ):
        raise ValueError("El user_id no puede estar vacío ni contener rutas.")

    # 0.6. Las funciones posteriores reciben siempre el ID ya limpio.
    return normalized_id


# 1. Define el estado que circula entre los nodos de LangGraph.
class MemoryState(TypedDict):
    """Estado de una conversación con memoria corta y transversal.

    ``add_messages`` hace que cada nodo agregue o actualice mensajes por su ID,
    en vez de reemplazar accidentalmente todo el historial.
    """

    # Historial completo del thread. ``Annotated[..., add_messages]`` asocia a
    # esta clave un reducer: cuando un nodo devuelve mensajes nuevos, LangGraph
    # los agrega por ID en lugar de sustituir la lista completa.
    messages: Annotated[list[BaseMessage], add_messages]

    # Recuerdos recuperados de Chroma únicamente para el turno actual.
    # ``NotRequired`` permite que la clave todavía no exista al iniciar el grafo.
    vector_memories: NotRequired[list[str]]

    # Copia recortada del historial que sí se enviará al modelo. Separarla de
    # ``messages`` impide que el recorte destruya el historial persistente.
    context_messages: NotRequired[list[BaseMessage]]

    # ID del último mensaje humano ya analizado por el extractor. Sirve para no
    # guardar dos veces la misma memoria si LangGraph reanuda un checkpoint.
    last_memory_extraction: NotRequired[str]


# 2. Describe y valida la salida estructurada del LLM extractor.
class ExtractedMemory(BaseModel):
    """Contrato que debe cumplir la respuesta del LLM extractor.

    Pydantic valida tipos, categorías e importancia antes de que el programa
    intente guardar la información en Chroma.
    """

    # ``Literal`` impide que el LLM invente categorías no admitidas.
    category: Literal[
        "personal",
        "profesional",
        "preferencias",
        "hechos_importantes",
        "none",
    ] = Field(description="Categoría de la memoria, o 'none' si no debe guardarse")

    # Texto breve que será vectorizado y recuperado en conversaciones futuras.
    content: str = Field(description="Hecho breve que se recordará")

    # ``ge`` y ``le`` obligan a que el valor esté entre 1 y 5.
    importance: int = Field(description="Importancia del 1 al 5", ge=1, le=5)


# 3. Administra los datos persistentes de un único usuario.
class ModernMemoryManager:
    """Gestiona metadatos de chats y memoria vectorial por usuario.

    Se crea una instancia por usuario. Por eso sus rutas, su colección Chroma y
    su SQLite pertenecen solamente a ese usuario.
    """

    def __init__(self, user_id: str):
        # 3.1. Valida el ID antes de usarlo como nombre de carpeta.
        self.user_id = _validate_user_id(user_id)

        # 3.2. Construye, por ejemplo, ``users/ana``. Todos los chats de Ana
        # compartirán esta carpeta, pero no la compartirán con otro usuario.
        self.user_dir = os.path.join(USERS_DIR, self.user_id)
        os.makedirs(self.user_dir, exist_ok=True)

        # 3.3. Chroma guardará aquí las memorias de largo plazo. Estas memorias
        # no están ligadas a un chat_id y, por tanto, cruzan conversaciones.
        self.chromadb_path = os.path.join(self.user_dir, "chromadb")
        self.vectorstore = self._init_vector_db()

        # 3.4. Prepara una cadena LangChain reutilizable. Todavía no llama al
        # modelo: la llamada ocurre al ejecutar ``extract_and_store_memory``.
        self.extraction_chain = self._init_extraction_system()

        # 3.5. ``chatbot.py`` conectará SqliteSaver con este archivo. SQLite
        # guardará los mensajes separados por thread_id (memoria de corto plazo).
        self.langgraph_db_path = os.path.join(
            self.user_dir,
            "langgraph_memory.db",
        )

    def _init_vector_db(self) -> Chroma | None:
        """Inicializa la base vectorial persistente de este usuario.

        Retorna un objeto Chroma listo para guardar/buscar, o ``None`` si falla.
        No inserta ninguna memoria todavía.
        """

        try:
            # 3.6. OpenAIEmbeddings sabe convertir tanto los recuerdos guardados
            # como las consultas futuras al mismo espacio numérico. Usar el
            # mismo modelo en ambos lados permite comparar su similitud.
            embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

            # 3.7. Chroma relaciona tres conceptos:
            # - collection_name: grupo lógico de documentos dentro de la BD;
            # - embedding_function: función que convierte texto en vectores;
            # - persist_directory: carpeta física para sobrevivir reinicios.
            return Chroma(
                # Cada usuario ya tiene un directorio distinto, por lo que una
                # colección con nombre estable es suficiente y evita nombres
                # inválidos derivados de correos u otros identificadores.
                collection_name="memorias",
                embedding_function=embeddings,
                persist_directory=self.chromadb_path,
            )
        except Exception as error:
            # 3.8. Chroma es una capacidad adicional. Si falta configuración o
            # no puede abrir su carpeta, retornamos None para que el chat todavía
            # pueda funcionar con su historial SQLite, aunque sin memoria larga.
            print(f"Error inicializando Chroma: {error}")
            return None

    def _init_extraction_system(self):
        """Construye la cadena que extrae una memoria estructurada.

        La cadena usa LCEL (LangChain Expression Language):
        prompt | modelo | parser

        La salida de cada componente se convierte en la entrada del siguiente.
        """

        try:
            # 3.9. Temperatura cero reduce variaciones porque esta tarea es de
            # clasificación/extracción, no de escritura creativa.
            extraction_llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)

            # 3.10. El parser conoce ExtractedMemory. Además de validar la salida,
            # puede generar instrucciones de formato para incluirlas en el prompt.
            memory_parser = PydanticOutputParser(pydantic_object=ExtractedMemory)

            # 3.11. PromptTemplate tiene dos tipos de variables:
            # - user_message cambia en cada invocación;
            # - format_instructions queda precargada desde el parser.
            extraction_prompt = PromptTemplate(
                template="""Analiza el siguiente mensaje del usuario y determina si contiene información importante que deba recordarse.

Categorías disponibles:
- personal: nombre, edad, ubicación, familia, etc.
- profesional: trabajo, empresa, proyectos o habilidades
- preferencias: gustos, disgustos o preferencias personales
- hechos_importantes: información relevante que debe recordarse

Mensaje del usuario: "{user_message}"

Si contiene información importante, extrae UNA memoria: la más importante.
Si no contiene información relevante, usa la categoría "none", contenido vacío e importancia 1.

{format_instructions}""",
                input_variables=["user_message"],
                partial_variables={
                    "format_instructions": memory_parser.get_format_instructions()
                },
            )

            # 3.12. El operador ``|`` no ejecuta aún la API. Construye este flujo:
            # diccionario -> prompt formateado -> AIMessage -> ExtractedMemory.
            return extraction_prompt | extraction_llm | memory_parser
        except Exception as error:
            # 3.13. Si no se puede construir, None activa después un extractor
            # manual basado en frases. Así se degrada la función sin cerrar todo.
            print(f"Error inicializando el extractor de memoria: {error}")
            return None

    # 4. Gestiona los metadatos JSON de los distintos chats del usuario.
    @property
    def _chats_metadata_path(self) -> str:
        """Calcula la ruta del índice de chats sin guardarla duplicada."""

        # ``@property`` permite usar ``self._chats_metadata_path`` como si fuera
        # un atributo, aunque la ruta se calcula al acceder a ella.
        return os.path.join(self.user_dir, "chats_meta.json")

    def get_user_chats(self) -> list[dict[str, Any]]:
        """Obtiene los chats del usuario, del más reciente al más antiguo.

        Este JSON solo contiene índice y presentación (ID, título, fechas y
        contador). Los mensajes reales viven en los checkpoints de SQLite.
        """

        try:
            # 4.1. Un usuario nuevo todavía no tiene índice: su lista es vacía.
            if not os.path.exists(self._chats_metadata_path):
                return []

            # 4.2. ``with`` cierra el archivo incluso si json.load falla.
            # UTF-8 conserva correctamente acentos y otros caracteres.
            with open(self._chats_metadata_path, "r", encoding="utf-8") as file:
                chats = json.load(file)

            # 4.3. Validación defensiva: el resto del código espera una lista de
            # diccionarios y no podría recorrer correctamente otro formato.
            if not isinstance(chats, list):
                raise ValueError("chats_meta.json debe contener una lista.")

            # 4.4. ``get`` usa texto vacío si falta updated_at. ``reverse=True``
            # coloca las fechas ISO más nuevas primero, útil para una barra lateral.
            chats.sort(key=lambda chat: chat.get("updated_at", ""), reverse=True)
            return chats
        except (OSError, json.JSONDecodeError, ValueError) as error:
            # 4.5. Se capturan errores de lectura, JSON corrupto o forma inválida.
            # Retornar [] evita que la interfaz completa deje de cargar.
            print(f"Error obteniendo chats: {error}")
            return []

    def _save_chats_metadata(self, chats: list[dict[str, Any]]) -> bool:
        """Sobrescribe el índice JSON con la lista de chats recibida."""

        try:
            # 4.6. El modo "w" crea el archivo si no existe y reemplaza su
            # contenido si existe. ``with`` asegura que los datos se cierren.
            with open(self._chats_metadata_path, "w", encoding="utf-8") as file:
                # indent=2 lo hace legible; ensure_ascii=False conserva "á" en
                # vez de escribirla como una secuencia escapada.
                json.dump(chats, file, indent=2, ensure_ascii=False)
            return True
        except OSError as error:
            # 4.7. El booleano permite que la futura UI sepa si el guardado falló.
            print(f"Error guardando metadatos de chats: {error}")
            return False

    def create_new_chat(self, first_message: str = "") -> str:
        """Añade los metadatos de un chat nuevo y devuelve su UUID."""

        # 4.8. uuid4 genera un ID independiente del título o del usuario. Así dos
        # chats con el mismo nombre siguen teniendo thread_id diferentes.
        chat_id = str(uuid.uuid4())

        # 4.9. Si ya se conoce el primer mensaje, el LLM intenta resumirlo como
        # título. Si no, se usa un marcador que podrá actualizarse más tarde.
        title = (
            self._generate_chat_title(first_message)
            if first_message.strip()
            else "Nuevo chat"
        )

        # 4.10. La misma fecha inicial representa creación y última modificación.
        now = _utc_now()

        # 4.11. Lee el índice anterior, agrega el nuevo diccionario y guarda la
        # lista completa. message_count comienza en cero porque aún no se ha
        # ejecutado necesariamente un turno del grafo.
        chats = self.get_user_chats()
        chats.append(
            {
                "chat_id": chat_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
            }
        )
        self._save_chats_metadata(chats)

        # El UUID será usado por chatbot.py para construir el thread_id.
        return chat_id

    def update_chat_metadata(
        self,
        chat_id: str,
        title: str | None = None,
        increment_messages: bool = False,
    ) -> bool:
        """Actualiza un chat existente o crea sus metadatos si aún no existen."""

        # 4.12. Trabaja sobre la representación JSON actual del usuario.
        chats = self.get_user_chats()

        # 4.13. Busca el diccionario cuyo ID coincide. ``get`` evita KeyError si
        # un registro viejo o incompleto no contiene chat_id.
        for chat in chats:
            if chat.get("chat_id") == chat_id:
                # Un título None o vacío significa "no cambiar el título".
                if title:
                    chat["title"] = title

                # El contador registra turnos procesados, no tokens ni recuerdos.
                if increment_messages:
                    chat["message_count"] = chat.get("message_count", 0) + 1

                # Toda actualización mueve el chat al inicio en la próxima lectura.
                chat["updated_at"] = _utc_now()
                break
        else:
            # 4.14. Este ``else`` pertenece al ``for``: solo se ejecuta si el
            # bucle terminó sin ``break``, es decir, si el chat no fue encontrado.
            if not chat_id:
                return False
            now = _utc_now()
            chats.append(
                {
                    "chat_id": chat_id,
                    "title": title or "Chat sin título",
                    "created_at": now,
                    "updated_at": now,
                    "message_count": 1 if increment_messages else 0,
                }
            )

        # 4.15. La operación solo se considera exitosa si el JSON pudo escribirse.
        return self._save_chats_metadata(chats)

    def delete_chat(self, chat_id: str) -> bool:
        """Elimina únicamente los metadatos JSON de un chat.

        Esta función no borra SQLite; la interfaz deberá llamar también a
        ``delete_chat_from_langgraph`` para eliminar el historial persistido.
        """

        # 4.16. La comprensión crea una lista nueva con todos los chats excepto
        # el solicitado. Si no existe, la lista queda simplemente igual.
        chats = [
            chat
            for chat in self.get_user_chats()
            if chat.get("chat_id") != chat_id
        ]
        return self._save_chats_metadata(chats)

    def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """Obtiene los metadatos de un chat o ``None`` si no existe."""

        # 4.17. La expresión generadora produce solo coincidencias. ``next`` toma
        # la primera y usa None como valor por defecto si no produjo ninguna.
        return next(
            (
                chat
                for chat in self.get_user_chats()
                if chat.get("chat_id") == chat_id
            ),
            None,
        )

    def _generate_chat_title(self, first_message: str) -> str:
        """Pide un título al LLM y ofrece uno local si la llamada falla."""

        # 4.18. El fallback no depende de red ni API: toma como máximo 30
        # caracteres y agrega puntos suspensivos solo si recortó el mensaje.
        fallback = (
            f"{first_message[:30]}..." if len(first_message) > 30 else first_message
        )

        # Un texto formado únicamente por espacios no sirve como título.
        if not first_message.strip():
            return "Nuevo chat"

        try:
            # 4.19. El prompt describe la tarea y deja {message} como variable.
            title_prompt = PromptTemplate(
                template="""Genera un título corto (máximo 4 o 5 palabras) para una conversación que comienza con este mensaje:

"{message}"

El título debe ser conciso, descriptivo y no incluir comillas.

Título:""",
                input_variables=["message"],
            )

            # 4.20. Temperatura cero busca títulos estables para la misma entrada.
            title_llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)

            # 4.21. ``prompt | llm`` es una cadena LCEL. ``invoke`` sí ejecuta la
            # llamada. Se limitan 200 caracteres para no gastar contexto inútil.
            response = (title_prompt | title_llm).invoke(
                {"message": first_message[:200]}
            )

            # 4.22. ChatOpenAI retorna AIMessage; su texto está en ``content``.
            # Los strip eliminan espacios y comillas que el modelo pudiera añadir.
            title = str(response.content).strip().strip('"\'')

            # La UI recibirá como máximo 50 caracteres, incluyendo "...".
            return title if len(title) <= 50 else f"{title[:47]}..."
        except Exception as error:
            # 4.23. Un fallo al titular no debe impedir crear o usar el chat.
            print(f"Error generando el título del chat: {error}")
            return fallback

    # 5. Guarda y consulta la memoria vectorial transversal.
    def save_vector_memory(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Convierte un texto en vector y lo guarda con sus metadatos.

        Retorna el ID creado cuando funciona y texto vacío cuando no se guardó.
        """

        # 5.1. Sin vectorstore no existe dónde guardar. Un texto vacío tampoco
        # aporta información útil y no debe generar una llamada de embeddings.
        if self.vectorstore is None or not text.strip():
            return ""

        try:
            # 5.2. Cada recuerdo tiene su propio ID. Este mismo valor se envía a
            # Chroma y se incluye en los metadatos para facilitar su inspección.
            memory_id = str(uuid.uuid4())

            # 5.3. ``dict`` crea una copia: al agregar campos internos no se
            # modifica accidentalmente el diccionario que entregó quien llamó.
            document_metadata = dict(metadata or {})
            document_metadata.update(
                {
                    "user_id": self.user_id,
                    "timestamp": _utc_now(),
                    "memory_id": memory_id,
                }
            )

            # 5.4. add_texts realiza internamente dos tareas:
            # a) OpenAIEmbeddings convierte ``text`` en un vector;
            # b) Chroma persiste texto, vector, ID y metadatos juntos.
            # La API recibe listas porque también permite insertar lotes.
            self.vectorstore.add_texts(
                texts=[text],
                metadatas=[document_metadata],
                ids=[memory_id],
            )
            return memory_id
        except Exception as error:
            print(f"Error guardando memoria vectorial: {error}")
            return ""

    def search_vector_memory(
        self,
        query: str,
        k: int = MAX_VECTOR_RESULTS,
    ) -> list[str]:
        """Busca por significado y devuelve hasta ``k`` recuerdos como texto."""

        # 5.5. Estas condiciones evitan consultas inválidas o innecesarias.
        if self.vectorstore is None or not query.strip() or k <= 0:
            return []

        try:
            # 5.6. similarity_search vectoriza la consulta con el mismo modelo y
            # pide a Chroma los k vectores más cercanos. Retorna Documents de
            # LangChain, no strings simples.
            documents = self.vectorstore.similarity_search(query, k=k)

            # 5.7. ``page_content`` contiene el texto original de cada recuerdo.
            # El chatbot solo necesita ese texto para construir el prompt.
            return [document.page_content for document in documents]
        except Exception as error:
            print(f"Error buscando memoria vectorial: {error}")
            return []

    def get_all_vector_memories(self) -> list[dict[str, Any]]:
        """Reconstruye una lista legible con todo lo almacenado en Chroma."""

        # 5.8. Sin Chroma inicializado, el usuario simplemente no tiene una lista
        # disponible para mostrar.
        if self.vectorstore is None:
            return []

        try:
            # 5.9. get retorna columnas paralelas: ids[i], documents[i] y
            # metadatas[i] describen la misma memoria.
            results = self.vectorstore.get()

            # ``or []`` también cubre el caso en que Chroma retorne None.
            documents = results.get("documents") or []
            ids = results.get("ids") or []
            metadatas = results.get("metadatas") or []

            # 5.10. zip empareja ID y documento; enumerate aporta el índice para
            # buscar los metadatos correspondientes. La comprobación de longitud
            # protege frente a resultados incompletos.
            return [
                {
                    "id": memory_id,
                    "content": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                }
                for index, (memory_id, document) in enumerate(zip(ids, documents))
            ]
        except Exception as error:
            print(f"Error obteniendo memorias vectoriales: {error}")
            return []

    # 6. Extrae una memoria nueva después de responder al usuario.
    def extract_and_store_memory(self, user_message: str) -> bool:
        """Extrae como máximo un hecho importante y lo guarda en Chroma.

        Retorna ``True`` únicamente si terminó guardando una memoria.
        """

        # 6.1. None indica que la cadena LLM no pudo inicializarse. En ese caso
        # se intenta reconocer patrones conocidos sin llamar al modelo.
        if self.extraction_chain is None:
            return self._extract_memory_manually(user_message)

        try:
            # 6.2. invoke inicia el flujo prompt -> LLM -> parser. Gracias al
            # parser, ``memory`` ya es ExtractedMemory y no un JSON sin validar.
            memory = self.extraction_chain.invoke({"user_message": user_message})

            # 6.3. "none" significa que no hay nada durable. También se descartan
            # memorias de importancia 1 para no llenar Chroma con conversación
            # cotidiana como saludos o preguntas puntuales.
            if memory.category == "none" or memory.importance < 2:
                return False

            # 6.4. El contenido resumido es lo que se vectoriza. Los metadatos no
            # participan directamente en la similitud, pero ayudan a auditarlo.
            memory_id = self.save_vector_memory(
                memory.content,
                {
                    "category": memory.category,
                    "importance": memory.importance,
                    "original_message": user_message[:200],
                },
            )

            # Un ID no vacío significa que Chroma confirmó la inserción.
            return bool(memory_id)
        except Exception as error:
            # 6.5. Incluye errores de API, parsing o validación. El fallback puede
            # rescatar mensajes explícitos como "recuerda que...".
            print(f"Error extrayendo memoria con el LLM: {error}")
            return self._extract_memory_manually(user_message)

    def _extract_memory_manually(self, user_message: str) -> bool:
        """Busca frases indicadoras sin usar un modelo de lenguaje."""

        # 6.6. Normaliza mayúsculas para que "ME GUSTA" y "me gusta" coincidan.
        message_lower = user_message.lower()

        # 6.7. Cada regla contiene:
        # (frases que la activan, categoría que se guardará, etiqueta legible).
        # Es intencionalmente simple: no comprende contexto como lo haría el LLM.
        memory_rules = [
            (["me llamo", "mi nombre es"], "personal", "Información personal"),
            (
                ["trabajo en", "trabajo como", "mi profesión"],
                "profesional",
                "Información profesional",
            ),
            (
                ["me gusta", "me encanta", "prefiero", "odio"],
                "preferencias",
                "Preferencia",
            ),
            (
                ["importante", "recuerda que", "no olvides"],
                "hechos_importantes",
                "Hecho importante",
            ),
        ]

        # 6.8. ``any`` se detiene cuando encuentra la primera frase presente.
        # También se detiene el bucle después de guardar la primera memoria, para
        # mantener la regla del ejercicio: máximo una memoria por mensaje.
        for phrases, category, label in memory_rules:
            if any(phrase in message_lower for phrase in phrases):
                memory_id = self.save_vector_memory(
                    f"{label}: {user_message}",
                    {"category": category, "source": "manual_fallback"},
                )
                return bool(memory_id)

        # Ninguna regla coincidió, por lo que no se efectuó inserción.
        return False


# 7. Lista y crea los directorios que representan usuarios del sistema.
class UserManager:
    """Gestor local y simplificado de usuarios; todavía no autentica.

    En este ejercicio, "existir" significa tener una carpeta dentro de users.
    No hay contraseñas, sesiones ni una base de datos de identidad todavía.
    """

    @staticmethod
    def get_users() -> list[str]:
        """Obtiene, en orden alfabético, los nombres de carpetas de usuarios."""

        # 7.1. Es defensivo: config.py normalmente ya creó USERS_DIR.
        if not os.path.exists(USERS_DIR):
            return []

        # 7.2. os.listdir incluye archivos y carpetas. El filtro isdir impide que
        # un archivo accidental sea tratado como usuario; sorted ordena la UI.
        return sorted(
            item
            for item in os.listdir(USERS_DIR)
            if os.path.isdir(os.path.join(USERS_DIR, item))
        )

    @staticmethod
    def user_exists(user_id: str) -> bool:
        """Comprueba si un ID válido ya corresponde a una carpeta."""

        try:
            # 7.3. La misma normalización usada al crear evita inconsistencias.
            normalized_id = _validate_user_id(user_id)
        except ValueError:
            return False

        # isdir exige que exista y que sea una carpeta, no solamente una ruta.
        return os.path.isdir(os.path.join(USERS_DIR, normalized_id))

    @staticmethod
    def create_user(user_id: str) -> bool:
        """Valida el ID y crea su directorio local."""

        try:
            # 7.4. Primero valida para no permitir escapar de USERS_DIR.
            normalized_id = _validate_user_id(user_id)

            # 7.5. exist_ok=True vuelve idempotente la operación: crear dos veces
            # el mismo usuario conserva su carpeta y retorna True.
            os.makedirs(os.path.join(USERS_DIR, normalized_id), exist_ok=True)
            return True
        except (OSError, ValueError) as error:
            # Puede fallar por un ID inválido o por permisos/sistema de archivos.
            print(f"Error creando usuario: {error}")
            return False
