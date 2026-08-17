'''En LangChain, un retriever (o recuperador) es un componente de software 
que actúa como un puente inteligente entre tus datos y un modelo de lenguaje (LLM).
Su función principal es buscar y extraer la información más relevante dentro de tu base 
de conocimiento en respuesta a una pregunta específica del usuario.'''
# gestionar información externa / de almacenes vectoriales
# dado un query busca y retorna un conjunto de documentos relevantes
# encapsula la busqueda para que la app recuperen objetos document de langchain

# en este ejemplo al haber ejecutado el archivo 6 almacen vetorial, ya se creo una bd y no es necesario crearla de nuevo chroma.sqlite3
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

#Abre la base de datos existente 

BASE_DIR = Path(__file__).resolve().parent

vectorstore = Chroma(   
    #transforma las consulta en embeddings
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory=str(BASE_DIR)
)

# instanciando un retriver apartir de una BD - se le envia las caracteristicas (tipo de busqueda , argumentos {diccionario})
# el objeto recupera info de una almacen de datos vectorial (bd  k = 2  ) 2 documentos
retriever = vectorstore.as_retriever(search_type = "similarity", search_kwargs = {"k": 2})

consulta = "Dónde se encuentra el local del cont en el que participa María Jiménez Campos?"
# obtiene los k2 documentos mas parecidos a la cosulta
resultados = retriever.invoke(consulta)

#top 3 de dcoumentos mas similares
print("Top 2 documentos mas similares a la consulta\n")
for i, doc in enumerate(resultados, start=1):
    print(f"\nDocumento {i}:")
    print(f" contenido : { doc.page_content}")
    #metadatos
    print(f"metadatos: {doc.metadata}")
    #print(f"Score de similitud: {resultado.metadata.get('score', 'N/A')}")

                  
