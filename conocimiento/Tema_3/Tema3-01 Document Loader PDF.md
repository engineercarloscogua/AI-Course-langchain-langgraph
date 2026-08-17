# Tema3-01 — Document Loader para PDF

**Archivo:** `Tema_3/1-document_loader.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Cargar y extraer texto de archivos PDF con LangChain  

---

## 📖 ¿Qué hace este archivo?

Introduce el concepto de **Document Loader**: una herramienta que conecta LangChain con fuentes de documentos (PDFs, bases de datos, APIs) y normaliza el contenido en objetos `Document` listos para procesar.

> Es el **primer paso** del pipeline RAG (Retrieval Augmented Generation).

---

## 💻 Código clave

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("ruta/al/archivo.pdf")
pages = loader.load()

# Cada página es un objeto Document
for i, page in enumerate(pages):
    print(f"=== Página {i+1} ===")
    print(f"Contenido: {page.page_content}")
    print(f"Metadatos: {page.metadata}")
    # → {'source': 'ruta.pdf', 'page': 0}
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `PyPDFLoader` | `langchain-community` + `pypdf` | Carga y parsea archivos PDF locales |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `PyPDFLoader(ruta)` | Clase | Cargador de PDFs locales |
| `.load()` | Método | Carga el PDF y retorna lista de `Document` |
| `.lazy_load()` | Método | Versión lazy (generador) para PDFs grandes |
| `page.page_content` | Atributo | Texto extraído de la página |
| `page.metadata` | Atributo | Dict con `source` (ruta), `page` (número) |

---

## 🧠 Concepto Clave: Objeto Document

> En LangChain, un `Document` es la unidad básica de información. Tiene dos partes:

```python
Document(
    page_content="El texto extraído de la página...",
    metadata={"source": "archivo.pdf", "page": 0}
)
```

---

## 🗺️ Ecosistema de Document Loaders en LangChain

| Loader | Fuente | Librería |
|---|---|---|
| `PyPDFLoader` | PDF local | `langchain-community` + `pypdf` |
| `PyPDFDirectoryLoader` | Carpeta de PDFs | `langchain-community` + `pypdf` |
| `GoogleDriveLoader` | Google Drive | `langchain-google-community` |
| `WebBaseLoader` | Páginas web | `langchain-community` + `beautifulsoup4` |
| `CSVLoader` | Archivos CSV | `langchain-community` |
| `TextLoader` | Archivos .txt | `langchain-community` |
| `UnstructuredFileLoader` | Múltiples formatos | `langchain-community` + `unstructured` |

---

## 🔄 Pipeline RAG — Posición del Document Loader

```
📄 Fuente de datos (PDF, Drive, Web...)
    ↓
Document Loader  ← ESTÁS AQUÍ
    ↓
Text Splitter → chunks
    ↓
Embedding Model → vectores
    ↓
Vector Store (ChromaDB, Pinecone...)
    ↓
Retriever → documentos relevantes
    ↓
LLM + contexto → respuesta
```

---

## 📝 Conceptos Aprendidos

- **Document Loader:** Abstracción que conecta LangChain con cualquier fuente de datos
- **`Document`:** Objeto estándar de LangChain con `page_content` y `metadata`
- **Metadatos:** Información sobre el origen del documento (útil para citar fuentes)
- **RAG:** Retrieval Augmented Generation — el patrón arquitectural de Tema 3

---

## ⚠️ Notas y Recomendaciones

> [!NOTE]
> `PyPDFLoader` solo funciona con PDFs que tienen texto real (seleccionable). Para PDFs escaneados (imágenes) necesitas OCR, como `UnstructuredPDFLoader` con Tesseract.

> [!TIP]
> Para procesar muchos PDFs de una carpeta usa `PyPDFDirectoryLoader` (ver [[Tema3-06 Vector Store Chroma]]).

> [!WARNING]
> Pasar un PDF completo directamente al LLM sin dividirlo consume muchos tokens. Siempre usa un Text Splitter después (ver [[Tema3-03 Text Splitter Parte 1]]).

---

## 🔗 Relaciones

- Anterior → [[Tema2-11 Proyecto CV Analyzer]]
- Siguiente → [[Tema3-02 Google Drive Loader]]
- Problema de tokens → [[Tema3-03 Text Splitter Parte 1]]
- Uso en RAG completo → [[Tema3-06 Vector Store Chroma]]
- Ver también → [[Glosario RAG y LLM#RAG]]
