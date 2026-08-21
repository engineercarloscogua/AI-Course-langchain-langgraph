"""Panel Streamlit para administrar conocimiento normativo compartido.

La interfaz captura decisiones humanas: fuente, vigencia y reemplazo de una
versión. Todo procesamiento se delega a ``KnowledgeApplicationService``.
"""

import hmac
from pathlib import Path

import streamlit as st

from application.knowledge_service import (
    KnowledgeApplicationService,
    NormativeUpload,
)
from domain.models import DomainError, NormativeDocument


ADMIN_AUTH_KEY = "improved_knowledge_admin_authenticated"
ADMIN_FLASH_KEY = "improved_knowledge_admin_flash"

STATUS_LABELS = {
    "draft": "Borrador",
    "active": "Vigente y publicada",
    "superseded": "Reemplazada",
    "repealed": "Derogada",
}


def _show_flash() -> None:
    flash = st.session_state.pop(ADMIN_FLASH_KEY, None)
    if flash:
        level, message = flash
        getattr(st, level)(message)


def _require_admin(configured_password: str) -> bool:
    """Protege operaciones que afectan el conocimiento de todos los usuarios."""

    if not configured_password:
        st.warning(
            "El panel está deshabilitado hasta configurar "
            "`KNOWLEDGE_ADMIN_PASSWORD` en el archivo `.env`."
        )
        return False

    if st.session_state.get(ADMIN_AUTH_KEY) is True:
        if st.button("Cerrar sesión administrativa"):
            st.session_state[ADMIN_AUTH_KEY] = False
            st.rerun()
        return True

    st.subheader("Acceso administrativo")
    with st.form("knowledge_admin_login"):
        candidate = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")
    if submitted:
        if hmac.compare_digest(candidate, configured_password):
            st.session_state[ADMIN_AUTH_KEY] = True
            st.rerun()
        st.error("La contraseña administrativa no es correcta.")
    return False


def _upload_form(service: KnowledgeApplicationService) -> None:
    """Carga una nueva versión; publicar y reemplazar son decisiones explícitas."""

    st.subheader("Cargar una norma")
    st.caption(
        "Usa preferiblemente PDF digitales de una fuente oficial. Los documentos "
        "escaneados sin texto requieren OCR antes de cargarlos."
    )
    with st.form("normative_document_upload", clear_on_submit=False):
        uploaded = st.file_uploader("Documento PDF", type=["pdf"])
        title = st.text_input(
            "Título oficial",
            placeholder="Código Nacional de Tránsito Terrestre",
        )
        first, second, third = st.columns(3)
        norm_type = first.selectbox(
            "Tipo",
            ["Ley", "Decreto", "Resolución", "Circular", "Sentencia", "Otro"],
        )
        norm_number = second.text_input("Número", placeholder="769")
        norm_year_text = third.text_input("Año", placeholder="2002")

        jurisdiction = st.text_input("Jurisdicción", value="Colombia")
        logical_key = st.text_input(
            "Clave normativa estable (opcional)",
            placeholder="colombia-ley-769-2002",
            help=(
                "Usa la misma clave al cargar una versión nueva para que el "
                "sistema pueda reemplazar la vigente sin borrar su historial."
            ),
        )
        version_label = st.text_input(
            "Versión",
            placeholder="Texto actualizado al 21/08/2026",
        )
        source_url = st.text_input(
            "URL de la fuente oficial",
            placeholder="https://www.suin-juriscol.gov.co/...",
        )
        date_from, date_to = st.columns(2)
        effective_from = date_from.text_input(
            "Vigente desde (opcional)",
            placeholder="AAAA-MM-DD",
        )
        effective_to = date_to.text_input(
            "Vigente hasta (opcional)",
            placeholder="AAAA-MM-DD",
        )
        publish = st.checkbox(
            "Publicar después de procesar",
            value=True,
            help="Si falla embeddings, el documento queda guardado como borrador.",
        )
        replace = st.checkbox(
            "Marcar como reemplazadas las versiones vigentes con la misma clave",
            value=True,
            disabled=not publish,
        )
        submitted = st.form_submit_button(
            "Procesar documento",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return
    if uploaded is None:
        st.error("Selecciona un archivo PDF.")
        return

    try:
        norm_year = int(norm_year_text) if norm_year_text.strip() else None
    except ValueError:
        st.error("El año debe contener solamente números.")
        return

    try:
        with st.spinner("Extrayendo artículos y preparando el índice normativo…"):
            outcome = service.ingest_pdf(
                NormativeUpload(
                    filename=uploaded.name,
                    content=uploaded.getvalue(),
                    title=title,
                    norm_type=norm_type,
                    norm_number=norm_number,
                    norm_year=norm_year,
                    jurisdiction=jurisdiction,
                    version_label=version_label,
                    source_url=source_url,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    logical_key=logical_key,
                ),
                publish=publish,
                replace_active_versions=replace,
            )
        if outcome.warning:
            st.warning(outcome.warning)
        else:
            st.success(
                f"«{outcome.document.title}» se guardó con estado "
                f"{STATUS_LABELS[outcome.document.status].lower()}."
            )
    except DomainError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"No fue posible procesar el documento: {type(error).__name__}: {error}")


def _document_caption(document: NormativeDocument) -> str:
    number = f" {document.norm_number}" if document.norm_number else ""
    year = f" de {document.norm_year}" if document.norm_year else ""
    return f"{document.norm_type}{number}{year} · {document.jurisdiction}"


def _render_document(
    service: KnowledgeApplicationService,
    document: NormativeDocument,
) -> None:
    """Muestra trazabilidad y operaciones seguras para una sola versión."""

    label = f"{STATUS_LABELS[document.status]} · {document.title} · {document.version_label}"
    with st.expander(label):
        st.markdown(f"**{_document_caption(document)}**")
        st.caption(
            f"Clave: `{document.logical_key}` · {document.chunk_count} fragmentos · "
            f"SHA-256: `{document.checksum_sha256[:16]}…`"
        )
        validity = (
            f"{document.effective_from or 'sin fecha inicial'} → "
            f"{document.effective_to or 'sin fecha final'}"
        )
        st.caption(f"Vigencia declarada: {validity}")
        if document.source_url:
            st.markdown(f"[Abrir fuente oficial]({document.source_url})")

        pdf_path = Path(document.stored_path)
        if pdf_path.is_file():
            st.download_button(
                "Descargar PDF almacenado",
                data=pdf_path.read_bytes(),
                file_name=document.original_filename,
                mime="application/pdf",
                key=f"download_norm_{document.document_id}",
            )

        action, danger = st.columns(2)
        with action:
            if document.status != "active":
                replace = st.checkbox(
                    "Reemplazar versión vigente",
                    value=True,
                    key=f"replace_on_publish_{document.document_id}",
                )
                if st.button(
                    "Publicar como vigente",
                    key=f"publish_norm_{document.document_id}",
                    use_container_width=True,
                ):
                    try:
                        service.publish_document(
                            document.document_id,
                            replace_active_versions=replace,
                        )
                        st.session_state[ADMIN_FLASH_KEY] = (
                            "success",
                            f"Se publicó «{document.title}».",
                        )
                        st.rerun()
                    except DomainError as error:
                        st.error(str(error))
            else:
                withdrawal = st.selectbox(
                    "Motivo del retiro",
                    options=["superseded", "repealed", "draft"],
                    format_func=lambda value: STATUS_LABELS[value],
                    key=f"withdrawal_status_{document.document_id}",
                )
                if st.button(
                    "Retirar sin borrar historial",
                    key=f"withdraw_norm_{document.document_id}",
                    use_container_width=True,
                ):
                    try:
                        service.deactivate_document(document.document_id, withdrawal)
                        st.session_state[ADMIN_FLASH_KEY] = (
                            "success",
                            f"«{document.title}» fue retirada del RAG vigente.",
                        )
                        st.rerun()
                    except DomainError as error:
                        st.error(str(error))

        with danger:
            confirmed = st.checkbox(
                "Confirmo la eliminación física",
                key=f"confirm_delete_norm_{document.document_id}",
            )
            if st.button(
                "Eliminar permanentemente",
                key=f"delete_norm_{document.document_id}",
                disabled=not confirmed,
                type="primary",
                use_container_width=True,
            ):
                try:
                    service.delete_document_permanently(document.document_id)
                    st.session_state[ADMIN_FLASH_KEY] = (
                        "success",
                        f"Se eliminó permanentemente «{document.title}».",
                    )
                    st.rerun()
                except DomainError as error:
                    st.error(str(error))


def _document_catalog(service: KnowledgeApplicationService) -> None:
    st.subheader("Versiones registradas")
    documents = service.list_documents()
    if not documents:
        st.info("Todavía no hay documentos en la base normativa.")
        return

    counts = {
        status: sum(document.status == status for document in documents)
        for status in STATUS_LABELS
    }
    columns = st.columns(4)
    for column, status in zip(columns, STATUS_LABELS, strict=True):
        column.metric(STATUS_LABELS[status], counts[status])

    selected_statuses = st.multiselect(
        "Filtrar por estado",
        options=list(STATUS_LABELS),
        default=list(STATUS_LABELS),
        format_func=lambda value: STATUS_LABELS[value],
    )
    for document in documents:
        if document.status in selected_statuses:
            _render_document(service, document)


def render_knowledge_admin(
    service: KnowledgeApplicationService,
    configured_password: str,
) -> None:
    """Compone la vista administrativa completa."""

    st.title("📚 Base normativa compartida")
    st.caption(
        "Carga y versiona fuentes oficiales sin mezclarlas con la memoria "
        "personal de los usuarios."
    )
    _show_flash()
    if not _require_admin(configured_password):
        return

    _upload_form(service)
    st.divider()
    _document_catalog(service)
