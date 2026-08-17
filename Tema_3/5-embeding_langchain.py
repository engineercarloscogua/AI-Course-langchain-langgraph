'''En LangChain, un embedding es una técnica que convierte texto 
(palabras, frases o documentos) en una lista de números. 
Estos números, llamados vectores, capturan el significado 
semántico o la "vibra" del texto y no solo las palabras exactas.'''
from langchain_community.document_loaders.parsers import OpenAIWhisperParser
from langchain_openai import OpenAIEmbeddings
import numpy as np

# crear las incrustaciones es gratis con el modelo text-embedding-3-large
#objeto
emdeddings = OpenAIEmbeddings(model ="text-embedding-3-large")

texto1 = "PAris es un buen lugar para tener mascotas"
texto2 = "Paris es la capital de francia"

#textos tranformados en vectores
vec1 = emdeddings.embed_query(texto1)
vec2 = emdeddings.embed_query(texto2)

# evaluar - calcular cosen similarity para ver si son similares los angulos entre los 2 vectores
cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1)*np.linalg.norm(vec2))
# entre más cercano a uno hay mayor similutd
print(f"similitud entre v1 y v2 es : {cos_sim:.3f}")
print("segunda medición", np.dot(vec1,vec2))