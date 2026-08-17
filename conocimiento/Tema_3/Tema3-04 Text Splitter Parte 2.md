# Tema3-04 — Text Splitter Parte 2 (RecursiveCharacterTextSplitter)

**Archivo:** `Tema_3/4-text_splitters_parte2.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Dividir documentos en chunks y procesarlos con LLM  

---

## 📖 ¿Qué hace este archivo?

Muestra la solución correcta al problema del contexto: usar `RecursiveCharacterTextSplitter` para dividir el PDF en chunks manejables y procesar cada uno por separado con el LLM, luego combinar los resultados en un resumen final.

---

## 💻 Código clave

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Dividir texto en chunks con solapamiento
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=10000,    # máximo 10,000 caracteres por chunk
    chunk_overlap=200    # 200 caracteres de superposición entre chunks
)
chunks = text_splitter.split_documents(pages)

# Procesar cada chunk con el LLM
summaries = []
for i, chunk in enumerate(chunks):
    if i > 10:  # procesar solo 10 chunks
        break
    response = llm.invoke(f"Resume: {chunk.page_content}")
    summaries.append(response.content)

# Combinar todos los resúmenes en uno final
final_summary = llm.invoke(f"Sintetiza: {' '.join(summaries)}")
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `PyPDFLoader` | `langchain-community` + `pypdf` | Cargar PDF |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |
| `RecursiveCharacterTextSplitter` | `langchain-text-splitters` | Dividir texto inteligentemente en chunks |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `RecursiveCharacterTextSplitter` | Clase | Splitter inteligente que respeta separadores naturales |
| `chunk_size` | Parámetro | Tamaño máximo de cada chunk en caracteres |
| `chunk_overlap` | Parámetro | Caracteres de superposición entre chunks consecutivos |
| `separators` | Parámetro | Lista de separadores en orden de prioridad |
| `.split_documents(pages)` | Método | Divide lista de Documents en chunks |
| `.split_text(texto_str)` | Método | Divide un string en lista de strings |

---

## 🧠 Concepto Clave: RecursiveCharacterTextSplitter

> Es el splitter **más recomendado** en LangChain. Intenta dividir en separadores naturales del texto en orden de prioridad:
> 1. `\n\n` (párrafos)  
> 2. `\n` (líneas)  
> 3. ` ` (palabras)  
> 4. `""` (caracteres individuales — último recurso)

---

## 🧠 Concepto Clave: chunk_overlap

> El **solapamiento** hace que cada chunk tenga los últimos N caracteres del chunk anterior. Esto asegura que el contexto no se pierda en los bordes.

```
Chunk 1: [==============================] (10,000 chars)
Chunk 2:                             [==[==============================]
         ← solapamiento de 200 chars →

Ambos chunks comparten los 200 chars del borde → el LLM no pierde contexto
```

---

## 🔄 Patrón: Map-Reduce con LLM

```
PDF completo
    ↓ split_documents()
[chunk1, chunk2, ..., chunkN]
    ↓ Map: resume cada chunk individualmente
[resumen1, resumen2, ..., resumenN]
    ↓ Reduce: combina todos los resúmenes
Resumen final coherente
```

---

## 📊 Parámetros recomendados por caso de uso

| Caso de uso | chunk_size | chunk_overlap |
|---|---|---|
| RAG / Búsqueda semántica | 500–1500 chars | 100–200 chars |
| Resumen de documentos | 5000–15000 chars | 200–500 chars |
| Código fuente | 1500–3000 chars | 300 chars |
| Noticias cortas | 200–500 chars | 50 chars |

---

## 📝 Conceptos Aprendidos

- **Chunking:** Dividir texto largo en fragmentos manejables
- **`chunk_size`:** Límite de tamaño de cada fragmento
- **`chunk_overlap`:** Evitar perder contexto en los bordes de los chunks
- **Map-Reduce:** Patrón para procesar documentos largos: mapear por chunk, luego reducir
- **`langchain-text-splitters`:** Paquete independiente de LangChain 0.2+ para splitters

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Para RAG, usa `chunk_size` entre 500-1500 caracteres. Chunks más pequeños = búsquedas más precisas. Chunks más grandes = más contexto por chunk.

> [!NOTE]
> En LangChain 0.2+, los text splitters se movieron al paquete independiente `langchain-text-splitters`. El import desde `langchain_community` puede mostrar deprecation warnings.

> [!TIP]
> Para el archivo 6 (vector store), usa `chunk_size=1000` y `separators=[". \n", "\n", " "]` para que los chunks terminen en oraciones completas.

---

## 🔗 Relaciones

- Anterior → [[Tema3-03 Text Splitter Parte 1]]
- Siguiente → [[Tema3-05 Embeddings OpenAI]]
- Uso en RAG → [[Tema3-06 Vector Store Chroma]]
- Más tipos de splitters → [[Librerías y Dependencias#Text Splitters]]
