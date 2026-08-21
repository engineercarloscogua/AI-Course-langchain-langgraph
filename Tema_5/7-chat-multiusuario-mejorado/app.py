r"""Punto de entrada de Streamlit del proyecto mejorado.

Ejecutar desde la raíz del repositorio:

    .\venv\Scripts\python.exe -m streamlit run .\Tema_5\7-chat-multiusuario-mejorado\app.py --server.port 8512
"""

# 1. ``find_dotenv`` (usado internamente) busca también en carpetas padre. Por
# eso la misma clave de la raíz sirve sin copiar secretos dentro del ejercicio.
from dotenv import load_dotenv


# Debe ejecutarse antes de importar ``config``: Settings lee en ese momento las
# variables opcionales de modelo, temperatura y límites.
load_dotenv()

import streamlit as st  # noqa: E402

from application.bootstrap import ApplicationContainer, build_application  # noqa: E402
from config import SETTINGS  # noqa: E402
from presentation.knowledge_admin_ui import render_knowledge_admin  # noqa: E402
from presentation.streamlit_ui import (  # noqa: E402
    KNOWLEDGE_VIEW,
    initialize_selection,
    render_conversation,
    render_sidebar,
    render_view_selector,
)

st.set_page_config(
    page_title=SETTINGS.page_title,
    page_icon=SETTINGS.page_icon,
    layout="wide",
)


# 2. Streamlit reejecuta este archivo en cada clic. Cachear el contenedor evita
# reconstruir el agente y reabrir las conexiones SQLite en cada rerun.
@st.cache_resource(show_spinner="Preparando agente y memorias…")
def get_application() -> ApplicationContainer:
    """Construye los recursos compartidos una sola vez por proceso."""

    return build_application()


def main() -> None:
    """Compone la página sin contener reglas de negocio."""

    try:
        container = get_application()
    except Exception as error:
        # Esta captura cubre SOLAMENTE la inicialización: clave ausente, archivo
        # SQLite sin permisos o dependencia incompatible. Antes envolvía toda la
        # UI y por eso un error de widget mostraba una sugerencia engañosa sobre
        # OPENAI_API_KEY.
        st.error(
            "No fue posible iniciar la aplicación. "
            f"Detalle: {type(error).__name__}: {error}"
        )
        st.info(
            "Verifica OPENAI_API_KEY, las dependencias y que la carpeta runtime "
            "tenga permisos de escritura."
        )
        return

    selected_view = render_view_selector()
    if selected_view == KNOWLEDGE_VIEW:
        render_knowledge_admin(
            container.knowledge_service,
            SETTINGS.knowledge_admin_password,
        )
        return

    service = container.chat_service
    try:
        default_user, default_chat = service.bootstrap()
    except Exception as error:
        st.error(
            "No fue posible preparar usuarios y conversaciones. "
            f"Detalle: {type(error).__name__}: {error}"
        )
        return

    initialize_selection(service, default_user, default_chat)
    user_id, chat_id = render_sidebar(service)
    render_conversation(service, user_id, chat_id)


if __name__ == "__main__":
    main()
