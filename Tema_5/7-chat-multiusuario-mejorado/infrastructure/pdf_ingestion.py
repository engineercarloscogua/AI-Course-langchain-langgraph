"""Extracción y fragmentación jurídica de documentos PDF.

El módulo no conoce Streamlit, OpenAI ni la base de datos. Recibe bytes y
devuelve secciones de texto. Esta separación permite sustituir ``pypdf`` por un
servicio OCR sin cambiar el caso de uso que administra las normas.
"""

from io import BytesIO
import re

from pypdf import PdfReader

from domain.models import LegalSection, PDFPage, ValidationError


class PDFTextExtractor:
    """Extrae texto de PDF digitales sin realizar llamadas de red."""

    @staticmethod
    def _normalize(text: str) -> str:
        """Limpia artefactos comunes conservando párrafos y encabezados."""

        clean = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
        # Muchos PDF dividen una palabra con guion al final de la línea.
        clean = re.sub(r"(?<=\w)-\n(?=\w)", "", clean)
        clean = re.sub(r"[ \t]+\n", "\n", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean)
        return clean.strip()

    def extract(self, pdf_bytes: bytes) -> list[PDFPage]:
        """Devuelve páginas con texto o explica por qué se requiere OCR."""

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValidationError(
                    "El PDF está protegido con contraseña y no puede procesarse."
                )

            pages = [
                PDFPage(
                    page_number=index,
                    text=self._normalize(page.extract_text() or ""),
                )
                for index, page in enumerate(reader.pages, start=1)
            ]
        except ValidationError:
            raise
        except Exception as error:
            raise ValidationError(
                "No fue posible leer el PDF. Verifica que el archivo no esté "
                "dañado ni protegido."
            ) from error

        if not pages or not any(page.text for page in pages):
            raise ValidationError(
                "El PDF no contiene texto extraíble. Si es un documento "
                "escaneado, primero debe pasar por OCR."
            )
        return pages


class LegalDocumentChunker:
    """Divide una norma por artículos antes de aplicar límites de tamaño."""

    # Reconoce formas frecuentes: ARTÍCULO 1°, Articulo 12A. y ARTÍCULO
    # TRANSITORIO. La expresión se mantiene deliberadamente conservadora para
    # no confundir cualquier número del cuerpo con el inicio de otro artículo.
    _article_pattern = re.compile(
        r"(?im)^[ \t]*(ART[ÍI]CULO\s+"
        r"(?:\d+[A-Z]?(?:\s*[°ºo])?|TRANSITORIO|[A-ZÁÉÍÓÚÑ]+)\s*\.?)"
    )

    def __init__(self, max_characters: int):
        if max_characters < 1_000:
            raise ValueError("Cada fragmento jurídico debe admitir al menos 1000 caracteres.")
        self._max_characters = max_characters

    @staticmethod
    def _heading(content: str, article: str) -> str:
        """Obtiene un encabezado corto cuando aparece después del artículo."""

        remainder = content[len(article) :].lstrip(" .°ºo-–—\n")
        first_line = next((line.strip() for line in remainder.splitlines() if line.strip()), "")
        if 0 < len(first_line) <= 140 and first_line == first_line.upper():
            return first_line
        return ""

    @staticmethod
    def _cut_position(text: str, start: int, target: int) -> int:
        """Evita cortar palabras buscando un separador cercano al límite."""

        end = min(start + target, len(text))
        if end == len(text):
            return end
        lower_bound = start + int(target * 0.75)
        candidates = [
            text.rfind("\n\n", lower_bound, end),
            text.rfind(". ", lower_bound, end),
            text.rfind(" ", lower_bound, end),
        ]
        return max(candidates) + 1 if max(candidates) >= lower_bound else end

    def _split_oversized(self, section: LegalSection) -> list[LegalSection]:
        """Conserva el artículo en cada parte si una unidad es demasiado larga."""

        if len(section.content) <= self._max_characters:
            return [section]

        parts: list[str] = []
        overlap = min(300, self._max_characters // 10)
        start = 0
        while start < len(section.content):
            end = self._cut_position(section.content, start, self._max_characters)
            parts.append(section.content[start:end].strip())
            if end >= len(section.content):
                break
            start = max(end - overlap, start + 1)

        total = len(parts)
        return [
            LegalSection(
                article=section.article,
                heading=section.heading,
                page_start=section.page_start,
                page_end=section.page_end,
                content=f"{section.article} · parte {index}/{total}\n{part}",
            )
            for index, part in enumerate(parts, start=1)
        ]

    def chunk(self, pages: list[PDFPage]) -> list[LegalSection]:
        """Produce secciones ordenadas conservando continuaciones entre páginas."""

        raw_sections: list[LegalSection] = []
        current_article = "Preámbulo y disposiciones iniciales"
        current_parts: list[str] = []
        page_start = pages[0].page_number if pages else 1
        page_end = page_start

        def flush() -> None:
            nonlocal current_parts
            content = "\n\n".join(part for part in current_parts if part).strip()
            if not content:
                current_parts = []
                return
            raw_sections.append(
                LegalSection(
                    article=current_article,
                    heading=self._heading(content, current_article),
                    page_start=page_start,
                    page_end=page_end,
                    content=content,
                )
            )
            current_parts = []

        for page in pages:
            text = page.text.strip()
            if not text:
                continue

            matches = list(self._article_pattern.finditer(text))
            if not matches:
                current_parts.append(text)
                page_end = page.page_number
                continue

            prefix = text[: matches[0].start()].strip()
            if prefix:
                current_parts.append(prefix)
                page_end = page.page_number

            for index, match in enumerate(matches):
                # Todo lo acumulado pertenece al artículo anterior. Esto incluye
                # la continuación situada al inicio de la página actual.
                flush()
                current_article = match.group(1).strip().rstrip(".")
                page_start = page.page_number
                page_end = page.page_number
                next_start = (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(text)
                )
                current_parts = [text[match.start() : next_start].strip()]

        flush()

        sections = [
            split
            for section in raw_sections
            for split in self._split_oversized(section)
        ]
        if not sections:
            raise ValidationError("No fue posible obtener secciones útiles del PDF.")
        return sections
