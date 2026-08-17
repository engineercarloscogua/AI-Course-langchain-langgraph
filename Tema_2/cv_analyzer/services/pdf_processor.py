# =====================================================
# PROCESAMIENTO DE ARCHIVOS PDF
# =====================================================
#
# CAMBIO: Se reemplazó PyPDF2 por pypdf.
#
# PyPDF2 está DEPRECADO desde diciembre de 2022.
# El proyecto fue absorbido de vuelta en la librería
# original "pypdf". PyPDF2 ya no recibe actualizaciones
# ni correcciones de seguridad.
#
# Migración:
#   ANTES: import PyPDF2
#           pdf_reader = PyPDF2.PdfReader(...)
#
#   AHORA: from pypdf import PdfReader
#           pdf_reader = PdfReader(...)
#
# La API es prácticamente idéntica, solo cambia el import.
# Referencia: https://pypdf.readthedocs.io/en/stable/
# =====================================================

# ANTES (deprecado): import PyPDF2
from pypdf import PdfReader  # <-- CORRECCIÓN: PyPDF2 reemplazado por pypdf

from io import BytesIO  # Permite leer el archivo en memoria sin guardarlo en disco


def extraer_texto_pdf(archivo_pdf) -> str:
    """
    Extrae todo el texto de un archivo PDF página por página.

    Args:
        archivo_pdf: Objeto de archivo de Streamlit (UploadedFile).

    Returns:
        str: Texto completo del CV, o un mensaje de error si falla.
    """
    try:
        # ANTES (deprecado): pdf_reader = PyPDF2.PdfReader(BytesIO(archivo_pdf.read()))
        # AHORA: usamos PdfReader directamente desde pypdf
        pdf_reader = PdfReader(BytesIO(archivo_pdf.read()))

        texto_completo = ""

        # Itera por cada página y extrae el contenido de texto
        for numero_pagina, pagina in enumerate(pdf_reader.pages, 1):
            texto_pagina = pagina.extract_text()

            # Solo agrega la página si tiene contenido real (no vacía)
            if texto_pagina and texto_pagina.strip():
                texto_completo += f"\n--- PÁGINA {numero_pagina} ---\n"
                texto_completo += texto_pagina + "\n"

        # Elimina espacios al inicio y final para ahorrar tokens al enviar a la IA
        texto_completo = texto_completo.strip()

        # Si el PDF no tiene texto (por ejemplo, es un PDF escaneado/imagen)
        if not texto_completo:
            return "Error: El PDF parece estar vacío o contener solo imágenes."

        return texto_completo

    except Exception as e:
        return f"Error al procesar el archivo PDF: {str(e)}"