# Tema3-07 — Retrievers

**Archivo:** `Tema_3/7-retrievers.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Recuperador de documentos desde Vector Store existente  

---

## 📖 ¿Qué hace este archivo?

Muestra cómo usar una base de datos ChromaDB **ya existente** (el `chroma.sqlite3` creado en el archivo 6) sin necesidad de re-indexar. Convierte el vector store en un **Retriever** de LangChain para búsquedas encapsuladas.

---

## 💻 Código clave

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Abrir BD existente (NO re-indexa, ahorra tokens)
vectorstore = Chroma(
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory="ruta/donde/esta/chroma.sqlite3/"
)

# Convertir en Retriever de LangChain
retriever = vectorstore.as_retriever(
    search_type="similarity",     # tipo de búsqueda
    search_kwargs={"k": 2}        # retornar 2 documentos
)

# Invocar el retriever
consulta = "¿Dónde está el local de María Jiménez Campos?"
resultados = retriever.invoke(consulta)  # → lista de Document
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `Chroma` | `langchain-community` + `chromadb` | Abrir vector store existente |
| `OpenAIEmbeddings` | `langchain-openai` | Convertir la consulta en vector para buscar |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `Chroma(embedding_function, persist_directory)` | Constructor | Abre BD existente SIN re-indexar |
| `.as_retriever(search_type, search_kwargs)` | Método | Crea un Retriever desde el vector store |
| `retriever.invoke(consulta)` | Método | Retorna los k documentos más relevantes |
| `"similarity"` | search_type | Búsqueda por similitud del coseno (la más común) |
| `"mmr"` | search_type | Maximum Marginal Relevance — más diversidad en resultados |
| `{"k": N}` | search_kwargs | Número de documentos a retornar |

---

## 🧠 Concepto Clave: ¿Qué es un Retriever?

> Un Retriever es una **abstracción de LangChain** que encapsula cualquier fuente de búsqueda (vector store, base de datos, internet, etc.) con una interfaz uniforme.

```python
# Cualquier Retriever tiene la misma interfaz:
retriever.invoke(consulta)  # → list[Document]

# Pueden ser de tipos muy diferentes:
vectorstore.as_retriever()           # desde Vector Store
BM25Retriever.from_documents(docs)   # búsqueda TF-IDF clásica
WebResearchRetriever(...)            # búsqueda en internet
```

---

## 🆚 similarity_search vs as_retriever

```python
# Método directo en el vectorstore
resultados = vectorstore.similarity_search(query, k=2)

# Usando retriever (preferible en cadenas LCEL)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})
resultados = retriever.invoke(query)
```

| Aspecto | `similarity_search()` | `as_retriever()` |
|---|---|---|
| Tipo de retorno | `list[Document]` | Retorna un Retriever |
| Compatible con LCEL `\|` | No directamente | **Sí** |
| Uso recomendado | Búsquedas simples | Cadenas LCEL y RAG |

---

## 🔄 Tipos de Búsqueda disponibles

| `search_type` | Descripción | Cuándo usar |
|---|---|---|
| `"similarity"` | Retorna los K más similares | **Caso más común** |
| `"mmr"` | Maximum Marginal Relevance: similar pero más diverso | Cuando quieres evitar resultados repetitivos |
| `"similarity_score_threshold"` | Solo retorna docs por encima de un umbral de similitud | Cuando calidad > cantidad |

---

## 📝 Conceptos Aprendidos

- **Retriever:** Abstracción unificada de LangChain para recuperar documentos
- **`as_retriever()`:** Convierte cualquier vector store en un Retriever compatible con LCEL
- **Reutilizar BD existente:** Abrir con el constructor `Chroma()` no re-indexa (ahorra tokens y tiempo)
- **`search_type`:** Controla el algoritmo de búsqueda

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Usa siempre `as_retriever()` en lugar de `similarity_search()` cuando construyas cadenas LCEL. Los Retrievers son ciudadanos de primera clase en LCEL y soportan `.invoke()`, `.stream()` y `.batch()`.

> [!NOTE]
> Para RAG completo, el Retriever va en medio de la cadena: `retriever | prompt | llm | parser`

> [!TIP]
> Usa `search_type="mmr"` cuando noticias que los resultados son muy similares entre sí. MMR balancea relevancia con diversidad.

---

## 🔗 Relaciones

- Anterior → [[Tema3-06 Vector Store Chroma]]
- Siguiente → [[Tema3-08 Multi-Query Retriever]]
- Uso en RAG → [[Recomendaciones y Buenas Prácticas#Pipeline RAG Completo]]
- Comparación → [[Clases y Funciones Clave#Retriever]]
