"""Interfaz Streamlit del sistema de chat multiusuario.

Este archivo conecta la capa visual con las dos memorias del ejercicio:

* ``chatbot.py`` conserva cada conversación en checkpoints de LangGraph.
* ``memory_manager.py`` administra usuarios, metadatos y memorias vectoriales.

Streamlit vuelve a ejecutar el archivo después de cada interacción. Por eso los
objetos que deben sobrevivir entre reruns se guardan en ``st.session_state``.
"""

from datetime import datetime, timezone

import streamlit as st

from chatbot import ChatbotManager
from config import PAGE_ICON, PAGE_TITLE
from memory_manager import UserManager
from utils import (
    format_timestamp,
    get_memory_category_icon,
    truncate_text,
    validate_user_id,
)

# 1. Configura la página antes de crear cualquier elemento visual.
#
# Streamlit exige que set_page_config sea su primera llamada. ``wide`` deja
# espacio para mostrar el chat y el panel de memorias uno junto al otro.
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. Prepara el estado que debe sobrevivir a los reruns de Streamlit.
def init_session_state():
    """Crea una sola vez las claves utilizadas por la interfaz."""

    # Cada condición protege el valor que ya existía. Si se asignaran las claves
    # sin comprobarlas, cada clic olvidaría el usuario y el chat seleccionados.
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "memory_manager" not in st.session_state:
        st.session_state.memory_manager = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_memories" not in st.session_state:
        st.session_state.show_memories = False


# 3. Selecciona el espacio aislado de un usuario o crea uno nuevo.
def user_selection_sidebar():
    """Muestra en la barra lateral la selección y creación de usuarios."""

    st.sidebar.header("👤 Usuario")

    # 3.1. Cada subcarpeta válida de USERS_DIR representa un usuario existente.
    existing_users = UserManager.get_users()

    if existing_users:
        # La opción vacía evita seleccionar automáticamente al primer usuario.
        selected_user = st.sidebar.selectbox(
            "Seleccionar usuario:",
            [""] + existing_users,
            key="user_selector",
        )
        if selected_user and selected_user != st.session_state.current_user:
            # 3.2. ChatbotManager reutiliza una instancia por usuario. El chatbot
            # ya contiene su ModernMemoryManager, así que compartirlo evita abrir
            # dos clientes de Chroma para la misma carpeta persistente.
            chatbot = ChatbotManager.get_chatbot(selected_user)
            st.session_state.current_user = selected_user
            st.session_state.chatbot = chatbot
            st.session_state.memory_manager = chatbot.memory_manager
            st.session_state.current_chat = None
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.sidebar.info("No hay usuarios creados")

    # 3.3. El expander queda abierto cuando todavía no existe ningún usuario.
    with st.sidebar.expander("Crear nuevo usuario", expanded=not existing_users):
        new_user_id = st.text_input(
            "ID de usuario:",
            placeholder="usuario123",
            help="Solo letras, números, - y _",
            key="new_user_input",
        )
        if st.button("Crear Usuario", type="primary", key="create_user_btn"):
            if not new_user_id:
                st.error("Ingresa un ID de usuario")
            elif not validate_user_id(new_user_id):
                st.error("ID inválido. Solo letras, números, - y _")
            elif UserManager.user_exists(new_user_id):
                st.error("El usuario ya existe")
            else:
                # 3.4. Primero se crea su carpeta y luego los componentes de
                # LangGraph y Chroma asociados exclusivamente a ese usuario.
                if UserManager.create_user(new_user_id):
                    chatbot = ChatbotManager.get_chatbot(new_user_id)
                    st.session_state.current_user = new_user_id
                    st.session_state.chatbot = chatbot
                    st.session_state.memory_manager = chatbot.memory_manager
                    st.session_state.current_chat = None
                    st.session_state.chat_history = []
                    st.success(f"Usuario '{new_user_id}' creado")
                    st.rerun()
                else:
                    st.error("Error creando usuario")


# 4. Presenta los metadatos de chats guardados para el usuario activo.
def chat_history_sidebar():
    """Muestra el historial de chats y permite seleccionarlos o eliminarlos."""

    if not st.session_state.current_user:
        return

    st.sidebar.header("💬 Chats")
    memory_manager = st.session_state.memory_manager

    # 4.1. Un chat nuevo recibe un UUID aunque aún no tenga mensajes. Ese UUID
    # se convertirá después en parte del thread_id persistido por LangGraph.
    if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
        new_chat_id = memory_manager.create_new_chat()
        st.session_state.current_chat = new_chat_id
        st.session_state.chat_history = []
        st.rerun()

    st.sidebar.markdown("---")

    # 4.2. Esta lista procede del JSON de metadatos; los mensajes reales siguen
    # almacenados en SQLite y solo se leen al seleccionar un chat.
    chats = memory_manager.get_user_chats()
    if chats:
        st.sidebar.subheader("Historial")
        for chat in chats:
            chat_id = chat["chat_id"]
            title = chat["title"]
            message_count = chat.get("message_count", 0)
            updated_at = format_timestamp(chat["updated_at"])

            # 4.3. Cada fila reserva la mayor parte del ancho para seleccionar el
            # chat y una columna pequeña para eliminarlo.
            chat_container = st.sidebar.container()
            with chat_container:
                col1, col2 = st.columns([4, 1])
                with col1:
                    is_active = st.session_state.current_chat == chat_id
                    button_args = {
                        "label": f"💬 {truncate_text(title, 25)}",
                        "key": f"chat_{chat_id}",
                        "help": f"Mensajes: {message_count} | Actualizado: {updated_at}",
                        "use_container_width": True,
                    }

                    # El tipo secundario distingue visualmente el chat activo.
                    if is_active:
                        button_args["type"] = "secondary"
                    if st.button(**button_args):
                        if st.session_state.current_chat != chat_id:
                            st.session_state.current_chat = chat_id
                            st.session_state.chat_history = (
                                st.session_state.chatbot.get_conversation_history(chat_id)
                            )
                            st.rerun()
                with col2:
                    if st.button(
                        "🗑️",
                        key=f"delete_{chat_id}",
                        help="Eliminar chat",
                    ):
                        if memory_manager.delete_chat(chat_id):
                            # 4.4. El JSON y SQLite son persistencias separadas;
                            # eliminar el chat requiere limpiar ambas.
                            if st.session_state.chatbot:
                                st.session_state.chatbot.delete_chat_from_langgraph(chat_id)
                            if st.session_state.current_chat == chat_id:
                                st.session_state.current_chat = None
                                st.session_state.chat_history = []
                            st.rerun()

        st.sidebar.markdown(f"**Total de chats:** {len(chats)}")
    else:
        st.sidebar.info("No hay chats todavía.\nHaz clic en 'Nuevo Chat' para comenzar.")

# 5. Dibuja la pantalla de bienvenida o la conversación seleccionada.
def main_chat_interface():
    """Muestra la interfaz principal y recibe nuevos mensajes."""

    if not st.session_state.current_user:
        st.title(PAGE_TITLE)
        st.info("👈 Selecciona o crea un usuario en la barra lateral para comenzar")
        return

    chatbot = st.session_state.chatbot
    if not chatbot:
        st.error("Error inicializando chatbot")
        return

    # 5.1. Si no hay chat seleccionado, se muestra la bienvenida. El primer
    # mensaje crea tanto los metadatos como el thread que usará LangGraph.
    if not st.session_state.current_chat:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.title("🤖 Asistente IA")
            st.markdown(f"**Hola, {st.session_state.current_user}!**")
            st.markdown("¿En qué puedo ayudarte hoy?")
            st.markdown("### Puedes preguntarme sobre:")
            st.markdown(
                """
            - 💼 **Trabajo y proyectos**
            - 📚 **Aprender algo nuevo**
            - 🤔 **Resolver problemas**
            - 💡 **Ideas creativas**
            - 📋 **Planificación y tareas**
            """
            )
            st.markdown("</div>", unsafe_allow_html=True)

        user_input = st.chat_input("Comienza una nueva conversación...")
        if user_input:
            memory_manager = st.session_state.memory_manager
            new_chat_id = memory_manager.create_new_chat(user_input)
            st.session_state.current_chat = new_chat_id
            process_user_message(user_input)
        return

    # 5.2. Los metadatos proporcionan el título; el historial se consulta por
    # separado al checkpoint identificado por current_chat.
    current_chat_info = st.session_state.memory_manager.get_chat_info(
        st.session_state.current_chat
    )
    if not current_chat_info:
        st.error("Chat no encontrado")
        return

    st.title(f"💬 {current_chat_info['title']}")
    st.caption(f"Usuario: {st.session_state.current_user}")

    # 5.3. La lista se mantiene en session_state para no consultar SQLite en cada
    # dibujo. Un historial vacío se vuelve a consultar porque también representa
    # un chat nuevo que todavía no tiene checkpoint.
    if not st.session_state.chat_history:
        st.session_state.chat_history = chatbot.get_conversation_history(
            st.session_state.current_chat
        )

    # 5.4. Los roles preparados en chatbot.py se traducen a los componentes de
    # chat de Streamlit. Un timestamp ausente simplemente no muestra pie de fecha.
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                timestamp = format_timestamp(message.get("timestamp", ""))
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                        if timestamp:
                            st.caption(f"📅 {timestamp}")
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        if timestamp:
                            st.caption(f"📅 {timestamp}")
        else:
            st.info("Comienza la conversación escribiendo un mensaje.")

    user_input = st.chat_input("Escribe tu mensaje aquí...")
    if user_input:
        process_user_message(user_input)


# 6. Ejecuta un turno completo desde la interfaz hasta LangGraph.
def process_user_message(user_input: str):
    """Envía un mensaje al chatbot y presenta el resultado del turno."""

    # 6.1. Mostrar primero el mensaje hace que la interfaz responda visualmente
    # antes de esperar las llamadas al modelo y a la memoria vectorial. Se usa
    # UTC para que esta fecha coincida con la que chatbot.py guardará en SQLite.
    with st.chat_message("user"):
        st.write(user_input)
        st.caption(
            f"📅 {format_timestamp(datetime.now(timezone.utc).isoformat())}"
        )

    # 6.2. ModernChatbot.chat ejecuta los cuatro nodos y convierte cualquier
    # error esperado de API o persistencia en un diccionario success=False.
    with st.spinner("Pensando..."):
        response = st.session_state.chatbot.chat(user_input, st.session_state.current_chat)

    if response["success"]:
        with st.chat_message("assistant"):
            st.write(response["response"])
            caption_parts = [
                f"📅 {format_timestamp(datetime.now(timezone.utc).isoformat())}"
            ]
            if response.get("memories_used", 0) > 0:
                caption_parts.append(f"🧠 {response['memories_used']} memorias")
            if response.get("context_optimized"):
                caption_parts.append("⚡ Optimizado")
            st.caption(" | ".join(caption_parts))

        # 6.3. chat() ya incrementó message_count después de completar el grafo.
        # Aquí solo se vuelve a leer SQLite para reflejar el nuevo turno. Hacer
        # otro incremento en la UI contaría cada mensaje exitoso dos veces.
        st.session_state.chat_history = st.session_state.chatbot.get_conversation_history(
            st.session_state.current_chat
        )
        st.rerun()
    else:
        st.error(f"Error: {response['error']}")


# 7. Permite explorar la memoria transversal almacenada en Chroma.
def show_memory_interface(container=st):
    """Muestra, filtra y ordena las memorias vectoriales del usuario."""

    container.subheader("🧠 Memoria Vectorial")
    if container.button("Cerrar", key="close_memories"):
        st.session_state.show_memories = False
        st.rerun()
    if not st.session_state.memory_manager:
        container.error("No hay gestor de memoria disponible")
        return

    # 7.1. Chroma devuelve solo documentos de la colección del usuario activo.
    memories = st.session_state.memory_manager.get_all_vector_memories()
    if not memories:
        container.info(
            "No hay memorias guardadas todavía. El sistema guardará "
            "automáticamente información importante de tus conversaciones."
        )
        return

    # 7.2. Estas estadísticas describen resultados ya recuperados; no realizan
    # nuevas consultas ni llamadas al modelo.
    col1, col2, col3 = container.columns(3)
    with col1:
        st.metric("Total Memorias", len(memories))
    with col2:
        categories = [
            mem["metadata"].get("category", "sin_categoria") for mem in memories
        ]
        unique_categories = len(set(categories))
        st.metric("Categorías", unique_categories)
    with col3:
        high_importance = sum(
            1
            for mem in memories
            if mem["metadata"].get("importance", 0) >= 4
        )
        st.metric("Alta Importancia", high_importance)

    # 7.3. set elimina categorías repetidas y sorted mantiene un orden estable.
    categories = sorted(
        {
            mem["metadata"].get("category", "sin_categoria")
            for mem in memories
        }
    )
    selected_category = container.selectbox(
        "Filtrar por categoría:",
        ["Todas"] + categories,
    )

    # Se crea una lista nueva para no reordenar accidentalmente la devuelta por
    # el gestor cuando el filtro conserva todas las memorias.
    filtered_memories = list(memories)
    if selected_category != "Todas":
        filtered_memories = [
            mem
            for mem in memories
            if mem["metadata"].get("category") == selected_category
        ]

    # 7.4. Las tuplas ordenan primero por importancia y, en caso de empate, por
    # timestamp ISO. reverse=True coloca los valores mayores al comienzo.
    filtered_memories.sort(
        key=lambda memory: (
            memory["metadata"].get("importance", 0),
            memory["metadata"].get("timestamp", ""),
        ),
        reverse=True,
    )

    container.write(f"Mostrando {len(filtered_memories)} de {len(memories)} memorias")
    for memory in filtered_memories:
        category = memory["metadata"].get("category", "sin_categoria")
        timestamp = memory["metadata"].get("timestamp", "")
        importance = memory["metadata"].get("importance", 0)

        # 7.5. El título resume cada recuerdo sin ocultar el contenido completo
        # que permanece disponible dentro del expander.
        title_parts = [get_memory_category_icon(category)]
        title_parts.append(truncate_text(memory["content"], 60))
        if importance > 0:
            title_parts.append(f"({'⭐' * importance})")
        title = " ".join(title_parts)

        with container.expander(title, expanded=False):
            st.write(memory["content"])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**Categoría:** {category}")
            with col2:
                if importance > 0:
                    st.caption(f"**Importancia:** {'⭐' * importance}")
            with col3:
                st.caption(f"**Fecha:** {format_timestamp(timestamp)}")


# 8. Coordina los componentes anteriores en cada ejecución del script.
def main():
    """Construye la interfaz correspondiente al estado actual de la sesión."""

    init_session_state()

    user_selection_sidebar()

    if st.session_state.current_user:
        chat_history_sidebar()

        st.sidebar.markdown("---")
        st.sidebar.info(f"**Usuario:** {st.session_state.current_user}")

        if st.sidebar.button("🧠 Ver Todas las Memorias", use_container_width=True):
            st.session_state.show_memories = True

    # 8.1. Al abrir las memorias, el chat conserva más espacio porque es el
    # elemento principal. Al cerrarlas, vuelve a ocupar todo el ancho.
    if st.session_state.show_memories:
        chat_col, mem_col = st.columns([3, 2])
        with chat_col:
            main_chat_interface()
        with mem_col:
            show_memory_interface(container=mem_col)
    else:
        main_chat_interface()


if __name__ == "__main__":
    main()
