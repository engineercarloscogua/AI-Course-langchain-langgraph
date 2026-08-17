'''Un Multi-Query Retriever (recuperador de múltiples consultas) es una técnica avanzada 
de optimización para sistemas RAG que utiliza un LLM para automatizar 
el proceso de ingeniería de prompts sobre la pregunta del usuario.

Su función es tomar la pregunta original, redactarla de varias formas distintas
y ejecutar múltiples búsquedas simultáneas para asegurar que no se pase por alto 
ninguna información relevante.'''
# gestionar información externa / de almacenes vectoriales
# dado un query busca y retorna un conjunto de documentos relevantes
# encapsula la busqueda para que la app recuperen objetos document de langchain

# en este ejemplo al haber ejecutado el archivo 6 almacen vetorial, ya se creo una bd y no es necesario crearla de nuevo chroma.sqlite3
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic.retrievers.multi_query import MultiQueryRetriever



#Abre la base de datos existente 

BASE_DIR = Path(__file__).resolve().parent

vectorstore = Chroma(   
    #transforma las consulta en embeddings
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory=str(BASE_DIR)
)
# definir el modelo comercial a usar 0 para que sea más preciso
llm = ChatOpenAI(model = "gpt-4o-mini", temperature= 0)

# instanciando un retriver apartir de una BD - se le envia las caracteristicas (tipo de busqueda , argumentos {diccionario})
# el objeto recupera info de una almacen de datos vectorial (bd  k = 2  ) 2 documentos
base_retriever = vectorstore.as_retriever(search_type = "similarity", search_kwargs = {"k": 2})

# definiendo retriever avanzado - deriva la consulta del primer retriever
retriever = MultiQueryRetriever.from_llm(retriever= base_retriever , llm = llm)

consulta = "Dónde se encuentra el local del cont en el que participa María Jiménez Campos?"
# obtiene los k2 documentos mas parecidos a la cosulta
resultados = retriever.invoke(consulta)

#top 3 de dcoumentos mas similares
print("Top de documentos mas similares a la consulta\n")
for i, doc in enumerate(resultados, start=1):
    print(f"\nDocumento {i}:")
    print(f" contenido : { doc.page_content}")
    #metadatos
    print(f"metadatos: {doc.metadata}")
    #print(f"Score de similitud: {resultado.metadata.get('score', 'N/A')}")

                  
