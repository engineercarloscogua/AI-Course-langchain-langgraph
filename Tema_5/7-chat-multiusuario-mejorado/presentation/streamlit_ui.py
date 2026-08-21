"""Componentes visuales de la aplicación Streamlit.

Este archivo conoce widgets y ``session_state``, pero no abre bases de datos ni
construye modelos. Toda acción se expresa mediante ChatApplicationService.
"""

import streamlit as st

from application.chat_service import ChatApplicationService
from config import APP_BUILD
from domain.models import Chat, DomainError, User


# 1. Las claves tienen prefijo para no colisionar con futuros widgets.
ACTIVE_USER_KEY = "improved_active_user_id"
ACTIVE_CHAT_KEY = "improved_active_chat_id"
FLASH_KEY = "improved_flash_message"
VIEW_SELECTOR_KEY = "improved_main_view"
CHAT_VIEW = "Chat"
KNOWLEDGE_VIEW = "Administrar normas"


def render_view_selector() -> str:
    """Separa el chat cotidiano del panel que modifica conocimiento global."""

    return st.sidebar.radio(
        "Sección",
        options=[CHAT_VIEW, KNOWLEDGE_VIEW],
        key=VIEW_SELECTOR_KEY,
    )


def initialize_selection(
    service: ChatApplicationService,
    default_user: User,
    default_chat: Chat,
) -> None:
    """Repara la selección si es el primer arranque o se borró un recurso."""

    users = service.list_users()
    valid_user_ids = {user.user_id for user in users}

    if st.session_state.get(ACTIVE_USER_KEY) not in valid_user_ids:
        st.session_state[ACTIVE_USER_KEY] = default_user.user_id

    active_user_id = st.session_state[ACTIVE_USER_KEY]
    chats = service.list_chats(active_user_id)
    if not chats:
        chats = [service.create_chat(active_user_id)]

    valid_chat_ids = {chat.chat_id for chat in chats}
    if st.session_state.get(ACTIVE_CHAT_KEY) not in valid_chat_ids:
        fallback = default_chat if default_chat.chat_id in valid_chat_ids else chats[0]
        st.session_state[ACTIVE_CHAT_KEY] = fallback.chat_id


def _select_user(service: ChatApplicationService) -> str:
    """Dibuja selector/creación de usuarios y devuelve el ID activo."""

    st.sidebar.subheader("👤 Usuario")
    users = service.list_users()
    names_by_id = {user.user_id: user.display_name for user in users}
    user_ids = list(names_by_id)
    current_id = st.session_state[ACTIVE_USER_KEY]

    selected_id = st.sidebar.selectbox(
        "Seleccionar usuario",
        options=user_ids,
        index=user_ids.index(current_id),
        format_func=lambda user_id: names_by_id[user_id],
        # La clave cambia cuando cambia el usuario activo. El widget nuevo toma
        # ``index`` como selección inicial y nunca necesitamos escribir en su
        # session_state. Así desaparece por diseño la excepción que prohíbe
        # modificar la clave de un widget ya instanciado.
        key=f"improved_user_selector_{current_id}",
    )
    if selected_id != current_id:
        st.session_state[ACTIVE_USER_KEY] = selected_id
        chats = service.list_chats(selected_id)
        selected_chat = chats[0] if chats else service.create_chat(selected_id)
        st.session_state[ACTIVE_CHAT_KEY] = selected_chat.chat_id
        st.rerun()

    with st.sidebar.expander("Crear nuevo usuario"):
        with st.form("new_user_form", clear_on_submit=True):
            display_name = st.text_input(
                "Nombre visible",
                max_chars=80,
                placeholder="Ejemplo: Carlos",
            )
            submitted = st.form_submit_button("Crear usuario", use_container_width=True)
            if submitted:
                try:
                    user, chat = service.create_user(display_name)
                    st.session_state[ACTIVE_USER_KEY] = user.user_id
                    st.session_state[ACTIVE_CHAT_KEY] = chat.chat_id
                    st.session_state[FLASH_KEY] = (
                        "success",
                        f"Usuario {user.display_name} creado.",
                    )
                    st.rerun()
                except DomainError as error:
                    st.error(str(error))

    return st.session_state[ACTIVE_USER_KEY]


def _render_chat_list(service: ChatApplicationService, user_id: str) -> str:
    """Dibuja chats, creación y borrado seguro de la conversación activa."""

    st.sidebar.divider()
    title_column, button_column = st.sidebar.columns([3, 1])
    title_column.subheader("💬 Chats")
    if button_column.button("➕", help="Nueva conversación", use_container_width=True):
        chat = service.create_chat(user_id)
        st.session_state[ACTIVE_CHAT_KEY] = chat.chat_id
        st.rerun()

    chats = service.list_chats(user_id)
    active_chat_id = st.session_state[ACTIVE_CHAT_KEY]
    for chat in chats:
        button_type = "primary" if chat.chat_id == active_chat_id else "secondary"
        label = f"{chat.title}  ·  {chat.turn_count} turnos"
        if st.sidebar.button(
            label,
            key=f"open_chat_{chat.chat_id}",
            type=button_type,
            use_container_width=True,
        ):
            st.session_state[ACTIVE_CHAT_KEY] = chat.chat_id
            st.rerun()

    # La confirmación evita borrar una conversación con un clic accidental.
    with st.sidebar.expander("Eliminar conversación actual"):
        confirmed = st.checkbox(
            "Comprendo que se borrará todo su historial",
            key=f"confirm_delete_{active_chat_id}",
        )
        if st.button(
            "Eliminar definitivamente",
            disabled=not confirmed,
            type="primary",
            use_container_width=True,
        ):
            service.delete_chat(user_id, active_chat_id)
            remaining = service.list_chats(user_id)
            replacement = remaining[0] if remaining else service.create_chat(user_id)
            st.session_state[ACTIVE_CHAT_KEY] = replacement.chat_id
            st.session_state[FLASH_KEY] = (
                "success",
                "La conversación fue eliminada.",
            )
            st.rerun()

    return st.session_state[ACTIVE_CHAT_KEY]


def _render_memory_panel(service: ChatApplicationService, user_id: str) -> None:
    """Permite inspeccionar y borrar la memoria de largo plazo."""

    st.sidebar.divider()
    with st.sidebar.expander("🧠 Memoria de largo plazo"):
        try:
            memories = service.list_memories(user_id)
        except Exception as error:
            st.warning(f"No fue posible leer la memoria: {error}")
            return

        if not memories:
            st.caption("Todavía no hay datos duraderos guardados.")
            return

        st.caption(
            "Estos datos se comparten entre los chats del usuario y permanecen "
            "después de reiniciar la aplicación."
        )
        for memory in memories:
            st.markdown(f"**{memory.category}** · {memory.content}")
            st.caption(f"Clave: `{memory.key}` · importancia {memory.importance}/5")
            if st.button(
                "Olvidar",
                key=f"forget_{user_id}_{memory.key}",
                use_container_width=True,
            ):
                service.delete_memory(user_id, memory.key)
                st.session_state[FLASH_KEY] = (
                    "success",
                    f"Se eliminó el recuerdo {memory.key}.",
                )
                st.rerun()
            st.divider()


def render_sidebar(service: ChatApplicationService) -> tuple[str, str]:
    """Renderiza toda la navegación y devuelve usuario/chat seleccionados."""

    user_id = _select_user(service)
    chat_id = _render_chat_list(service, user_id)
    _render_memory_panel(service, user_id)
    return user_id, chat_id


def _render_flash_message() -> None:
    """Muestra una notificación una sola vez después de ``st.rerun``."""

    flash = st.session_state.pop(FLASH_KEY, None)
    if not flash:
        return
    level, message = flash
    getattr(st, level)(message)


def render_conversation(
    service: ChatApplicationService,
    user_id: str,
    chat_id: str,
) -> None:
    """Muestra el historial y procesa como máximo un nuevo turno."""

    st.title("🤖 Chat multiusuario mejorado")
    st.caption(
        "Agente con herramientas controladas, memoria persistente y arquitectura "
        f"por capas. · versión {APP_BUILD}"
    )
    _render_flash_message()

    try:
        history = service.history(user_id, chat_id)
    except DomainError as error:
        st.error(str(error))
        return

    if not history:
        st.info(
            "Comienza una conversación. Puedes contar varios datos en una sola "
            "frase y luego comprobarlos en **Memoria de largo plazo**."
        )

    for message in history:
        avatar = "👤" if message.role == "user" else "🤖"
        with st.chat_message(message.role, avatar=avatar):
            st.markdown(message.content)

    prompt = st.chat_input("Escribe tu mensaje…")
    if not prompt:
        return

    # La entrada se muestra inmediatamente mientras el backend trabaja.
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("El agente está pensando…"):
                reply = service.send_message(user_id, chat_id, prompt)
            st.markdown(reply.content)

        if reply.warning:
            st.session_state[FLASH_KEY] = ("warning", reply.warning)
        elif reply.memories_saved:
            st.session_state[FLASH_KEY] = (
                "success",
                f"Memoria actualizada: {reply.memories_saved} dato(s) guardado(s).",
            )
        st.rerun()
    except DomainError as error:
        st.error(str(error))
    except Exception as error:
        # Los errores inesperados se muestran completos en este proyecto
        # didáctico para facilitar el diagnóstico durante el curso.
        st.error(f"Error inesperado: {type(error).__name__}: {error}")
