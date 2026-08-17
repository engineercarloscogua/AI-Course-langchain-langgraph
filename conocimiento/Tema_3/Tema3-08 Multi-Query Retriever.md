# Tema3-08 — Multi-Query Retriever

**Archivo:** `Tema_3/8-multy-query-retriever.py`  
**Nivel:** 🔴 Avanzado  
**Tema:** Mejorar la recuperación generando múltiples variaciones de la consulta  

---

## 📖 ¿Qué hace este archivo?

Implementa el **Multi-Query Retriever**: una técnica avanzada donde el LLM genera automáticamente múltiples variaciones de la pregunta del usuario para hacer búsquedas más completas en el vector store, reduciendo el riesgo de perder documentos relevantes por cómo fue formulada la pregunta.

> ⚠️ El archivo usa `langchain_classic` que puede no estar disponible. El import correcto moderno es `langchain.retrievers.multi_query`.

---

## 💻 Código clave

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# ⚠️ Import en el archivo (puede fallar):
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

# ✅ Import correcto moderno:
# from langchain.retrievers.multi_query import MultiQueryRetriever

# Abrir BD existente
vectorstore = Chroma(
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory="ruta/"
)

# LLM para generar variaciones de la consulta
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Retriever base (el que hace la búsqueda real)
base_retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 2}
)

# Retriever avanzado: usa el LLM para reformular la consulta
retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

consulta = "¿Dónde está el local de María Jiménez Campos?"
resultados = retriever.invoke(consulta)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `Chroma` | `langchain-community` + `chromadb` | Vector store |
| `OpenAIEmbeddings` | `langchain-openai` | Embeddings para indexación y búsqueda |
| `ChatOpenAI` | `langchain-openai` | LLM para generar variaciones de consulta |
| `MultiQueryRetriever` | `langchain` | Retriever avanzado con múltiples consultas |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `MultiQueryRetriever` | Clase | Retriever que genera N variaciones de la consulta |
| `.from_llm(retriever, llm)` | Método de clase | Crea el multi-retriever desde un retriever base y un LLM |
| `retriever` | Parámetro | El retriever base que ejecuta la búsqueda real |
| `llm` | Parámetro | El LLM que genera las variaciones de la consulta |
| `retriever.invoke(consulta)` | Método | Ejecuta múltiples búsquedas y combina resultados únicos |

---

## 🧠 Cómo funciona MultiQueryRetriever

```
Consulta original:
"¿Dónde está el local de María Jiménez Campos?"
    ↓ LLM genera variaciones automáticamente
Variación 1: "Ubicación del local arrendado por María Jiménez Campos"
Variación 2: "Dirección del inmueble en contrato de María Jiménez"
Variación 3: "Local comercial María Jiménez Campos dirección"
    ↓ Se ejecutan 3 búsquedas en el vector store en paralelo
Resultados 1 + Resultados 2 + Resultados 3
    ↓ Se eliminan duplicados
Conjunto unificado de documentos únicos y relevantes
```

---

## 🆚 Retriever Simple vs Multi-Query Retriever

| Aspecto | Retriever Simple | Multi-Query Retriever |
|---|---|---|
| Consultas ejecutadas | 1 | N (generadas por el LLM) |
| Llamadas al LLM | 0 | 1 (para generar variaciones) |
| Llamadas al vector store | 1 | N |
| Cobertura | Limitada | Mayor |
| Costo | Bajo | Moderado |
| Cuándo usar | Consultas claras y específicas | Consultas ambiguas o complejas |

---

## 📝 Conceptos Aprendidos

- **Multi-Query Retriever:** Técnica de aumento de recuperación usando múltiples reformulaciones
- **Ingeniería de prompts automática:** El LLM reformula la consulta de formas distintas
- **Deduplicación:** Los resultados de múltiples búsquedas se combinan eliminando duplicados
- **Costo adicional:** Hay un costo de 1 llamada extra al LLM para generar las variaciones

---

## ⚠️ Notas y Recomendaciones

> [!WARNING]
> El import `from langchain_classic.retrievers.multi_query import MultiQueryRetriever` puede fallar. El import correcto es: `from langchain.retrievers.multi_query import MultiQueryRetriever`

> [!TIP]
> Usa `MultiQueryRetriever` cuando las consultas de los usuarios son ambiguas, usan jerga, o cuando los documentos usan terminología diferente a la de los usuarios.

> [!NOTE]
> Para ver las consultas generadas por el LLM, activa el logging: `import logging; logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)`

> [!TIP]
> Alternativa más avanzada: **RAG-Fusion** y **HyDE** (Hypothetical Document Embeddings) para mejorar aún más la recuperación.

---

## 🔗 Relaciones

- Anterior → [[Tema3-07 Retrievers]]
- Hacia el siguiente nivel → [[Recomendaciones y Buenas Prácticas#Técnicas Avanzadas de RAG]]
- Bug del import → [[Librerías Deprecadas y Alternativas#langchain_classic]]
- Glosario → [[Glosario RAG y LLM#Multi-Query Retriever]]
