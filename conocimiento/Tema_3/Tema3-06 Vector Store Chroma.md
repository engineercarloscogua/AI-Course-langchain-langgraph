# Tema3-06 — Vector Store con ChromaDB

**Archivo:** `Tema_3/6-almacen_vectorial_contratos.py`  
**Nivel:** 🔴 Avanzado  
**Tema:** Almacén de vectores, indexación de documentos y búsqueda semántica  

---

## 📖 ¿Qué hace este archivo?

Implementa el componente central del pipeline RAG: el **Vector Store**. Carga múltiples PDFs de contratos, los divide en chunks, los convierte en embeddings y los almacena en ChromaDB (una base de datos vectorial local). Luego realiza una búsqueda por similitud semántica.

---

## 💻 Código clave

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Cargar todos los PDFs de una carpeta
loader = PyPDFDirectoryLoader("Contratos/")
documentos = loader.load()

# 2. Dividir en chunks
text_splitter = RecursiveCharacterTextSplitter(
    separators=[".\n", "\n", " "],
    chunk_size=1000,
    chunk_overlap=200
)
docs_split = text_splitter.split_documents(documentos)

# 3. Crear el vector store (indexar = convertir a vectores + guardar)
vectorstore = Chroma.from_documents(
    docs_split,
    embedding=OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory="ruta/donde/guardar/"  # persiste en disco (SQLite)
)

# 4. Buscar por similitud semántica
consulta = "¿Dónde está el local del contrato de María Jiménez Campos?"
resultados = vectorstore.similarity_search(consulta, k=3)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `Chroma` | `langchain-community` + `chromadb` | Vector store local con SQLite |
| `OpenAIEmbeddings` | `langchain-openai` | Convertir texto en vectores |
| `PyPDFDirectoryLoader` | `langchain-community` + `pypdf` | Carga todos los PDFs de una carpeta |
| `RecursiveCharacterTextSplitter` | `langchain-text-splitters` | Dividir documentos en chunks |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `PyPDFDirectoryLoader(carpeta)` | Clase | Carga todos los PDFs de un directorio recursivamente |
| `Chroma.from_documents(docs, embedding, persist_directory)` | Método de clase | Crea y persiste el vector store desde documentos |
| `Chroma(embedding_function, persist_directory)` | Constructor | Abre un vector store **existente** (sin recrearlo) |
| `.from_documents(docs, embedding)` | Método | Indexa los documentos (crea embeddings y los guarda) |
| `.similarity_search(query, k=N)` | Método | Busca los N chunks más similares a la consulta |
| `.similarity_search_with_score(query, k=N)` | Método | Igual pero retorna también el score de similitud |
| `.as_retriever(...)` | Método | Convierte el vectorstore en un Retriever de LangChain |
| `persist_directory` | Parámetro | Ruta donde ChromaDB guarda `chroma.sqlite3` |

---

## 🔄 Flujo de Indexación (una sola vez)

```
PDFs en carpeta Contratos/
    ↓ PyPDFDirectoryLoader
Lista de Documents con page_content y metadata
    ↓ RecursiveCharacterTextSplitter
Lista de chunks (Documents más pequeños)
    ↓ OpenAIEmbeddings  ← llamadas a la API de OpenAI
Lista de vectores numéricos (3072 dimensiones c/u)
    ↓ Chroma.from_documents()
chroma.sqlite3  ← base de datos vectorial persistida en disco
```

---

## 🔄 Flujo de Consulta (cada vez que se pregunta algo)

```
consulta del usuario (texto)
    ↓ OpenAIEmbeddings.embed_query()
vector de la consulta (3072 dimensiones)
    ↓ búsqueda por similitud del coseno en ChromaDB
Top-K chunks más similares (Documents)
    ↓ (se envían al LLM como contexto)
Respuesta con información del contrato
```

---

## 🧠 Concepto Clave: Vector Store

> Un Vector Store es una base de datos especializada que almacena vectores y permite búsquedas de similitud extremadamente rápidas usando algoritmos como HNSW (Hierarchical Navigable Small World).

| Vector Store | Tipo | Cuándo usarlo |
|---|---|---|
| **ChromaDB** | Local | Desarrollo, proyectos pequeños, sin infra |
| **FAISS** | Local | Proyectos medianos, más rápido que Chroma |
| **Pinecone** | Cloud | Producción, escalabilidad alta |
| **Weaviate** | Cloud/Self-hosted | Producción, búsqueda híbrida |
| **pgvector** | PostgreSQL | Producción, ya tienes PostgreSQL |

---

## 🗂️ ChromaDB en detalle

```
persist_directory/
└── chroma.sqlite3   → base de datos SQLite con:
                       - Vectores (embeddings)
                       - Textos (page_content)
                       - Metadatos (source, page)
                       - Colecciones
```

> ⚠️ El archivo `chroma.sqlite3` en el proyecto pesa 2.8 MB — ya tiene los contratos indexados.

---

## 📝 Conceptos Aprendidos

- **Vector Store:** Base de datos especializada para búsqueda semántica
- **Indexación:** Proceso de convertir documentos en embeddings y guardarlos
- **`similarity_search()`:** Búsqueda por significado, no por palabras exactas
- **`k`:** Número de documentos más similares a retornar
- **`persist_directory`:** Hace que ChromaDB sobreviva entre ejecuciones del programa

---

## ⚠️ Notas y Recomendaciones

> [!IMPORTANT]
> La indexación con `Chroma.from_documents()` **llama a la API de OpenAI** para cada chunk. Si ya tienes el `chroma.sqlite3`, usa el constructor `Chroma(...)` directamente para no gastar tokens de nuevo (ver [[Tema3-07 Retrievers]]).

> [!WARNING]
> En versiones recientes de ChromaDB (>= 0.4.x), `persist_directory` **no necesita** llamar a `.persist()` manualmente. Los datos se guardan automáticamente.

> [!TIP]
> Para producción, considera migrar de ChromaDB a **Pinecone** o **pgvector** para mayor escalabilidad. ChromaDB es excelente para desarrollo y proyectos pequeños.

---

## 🔗 Relaciones

- Anterior → [[Tema3-05 Embeddings OpenAI]]
- Siguiente → [[Tema3-07 Retrievers]]
- Tabla de Vector Stores → [[Recomendaciones y Buenas Prácticas#Vector Stores en Producción]]
- Comparación → [[Librerías Deprecadas y Alternativas#ChromaDB]]
