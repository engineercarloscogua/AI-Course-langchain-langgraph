'''Un Document Loader (cargador de documentos) es una herramienta que extrae texto 
y metadatos de archivos en diferentes formatos para que puedan ser procesados por
una Inteligencia Artificial.Es el primer paso en el flujo de trabajo de aplicaciones 
como los sistemas RAG (Recuperación Aumentada por Generación).'''

'''¿Cuál es su función principal?
Los Modelos de Lenguaje (LLMs) solo entienden texto plano, pero las empresas guardan 
su información en formatos muy diversos. El Document Loader se encarga de:

Conectar: Acceder a la fuente de origen (un archivo local, una base de datos o una API en la nube).
Extraer: Leer el contenido ignorando el código o formato propietario.
Normalizar: Convertir todo ese contenido en un formato estándar de texto limpio estructurado, listo para el Text Splitter.'''


from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader

BASE_DIR = Path(__file__).resolve().parent
pdf_path = BASE_DIR / "Aplicación del marco ético de inteligencia artificial en Colombia en el sector educativo.pdf"
loader = PyPDFLoader(str(pdf_path))

pages = loader.load()

# visualizar los metodos que se pueden aplicar a docs
print(pages[0])

# ver contenido de las paginas

for i, page in enumerate(pages):
    print(f'=== Pagina == {i+1}===')
    print(f"Contenido : {page.page_content}")
    print(f"Metadatos: {page.metadata}")
