'''Un vector store (o almacén de vectores) es una base de datos especializada 
que guarda y organiza información basándose en su significado semántico. 
En LangChain, sirve como el "cerebro" para buscar datos por contexto, 
siendo el componente principal para implementar sistemas de respuesta automática con IA'''

from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parent
loader = PyPDFDirectoryLoader(str(BASE_DIR / "Contratos"))
documentos = loader.load() 

print(f"numero de documentos {len(documentos)}")

text_splitter = RecursiveCharacterTextSplitter(
    separators=[".\n", "\n", " "],
     chunk_size = 1000, 
     chunk_overlap = 200)

docs_split = text_splitter.split_documents(documentos)

print(f"numero de documentos divididos (chunks) {len(docs_split)}")

vectorstore = Chroma.from_documents(
    docs_split,
    embedding=OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory=str(BASE_DIR)
)

consulta = "Dónde se encuentra el local del cont en el que participa María Jiménez Campos?"
# devolver los chuks o fragmentos mas similares e la consulta
resultados = vectorstore.similarity_search(consulta, k=3)

#top 3 de dcoumentos mas similares
for i, doc in enumerate(resultados, start=1):
    print(f"\nDocumento {i}:")
    print(f" contenido : { doc.page_content}")
    #metadatos
    print(f"metadatos: {doc.metadata}")
    #print(f"Score de similitud: {resultado.metadata.get('score', 'N/A')}")
