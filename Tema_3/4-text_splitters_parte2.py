'''Un Text Splitter (divisor de texto) en LangChain es una herramienta diseñada
para dividir documentos o textos extensos en fragmentos más pequeños y manejables.
Es un paso esencial en los sistemas de búsqueda y en la arquitectura RAG 
(Generación Aumentada por Recuperación), ya que permite encajar el contenido 
dentro del límite de la ventana de contexto de un modelo de lenguaje (LLM) 
y facilita una recuperación de información más precisa'''

'''En LangChain, un chunk (o fragmento) es una porción o segmento pequeño de un texto más grande.
El proceso de dividir documentos extensos en partes más manejables se llama chunking y 
es fundamental en los sistemas de IA para evitar superar los límites de memoria de los modelos'''

'''Text Splitter (El proceso): Es el algoritmo o función que toma un documento largo
y lo corta en partes más pequeñas.
Chunk (El resultado): Es cada uno de los fragmentos individuales de texto que se obtienen
tras aplicar el text splitter.'''

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
#modulo independiente -------------------divide pdf de forma inteligente
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Cargar el documento PDF
BASE_DIR = Path(__file__).resolve().parent
pdf_path = BASE_DIR / "Aplicación del marco ético de inteligencia artificial en Colombia en el sector educativo.pdf"
loader = PyPDFLoader(str(pdf_path))
pages = loader.load()

# Dividir el texto en chunks(pedazo) mas pequeños
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=10000,
    # super posiscoón o solapamiento de 200 caracteres, para que tenga contexto del pedazo de texto aterior
    chunk_overlap=200
)
# división el texto pasandole las paginas
chunks = text_splitter.split_documents(pages)

# 3. Pasar el texto al LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
summaries = []

i = 0
# recorriendo solo hasta  10 fragmentos
for chunk in chunks:
    if i > 10:
        break
    response = llm.invoke(f"Haz un resumen de los puntos mas importantes del siguiente texto: {chunk.page_content}")
    # agrega el resumen a la lista
    summaries.append(response.content)
    i += 1

print(summaries)

final_summary = llm.invoke(f"Combina y sintetiza estos resumenes en un resumen coherente y completo: {" ".join(summaries)}")
print(final_summary.content)
