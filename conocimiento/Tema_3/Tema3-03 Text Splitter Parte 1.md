# Tema3-03 — Text Splitter Parte 1 (El Problema)

**Archivo:** `Tema_3/3-text_splitters_parte1.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Problema del contexto largo — por qué NO enviar PDFs completos al LLM  

---

## 📖 ¿Qué hace este archivo?

Este archivo está marcado como **"no ejecutar"** en el código. Su propósito es **educativo**: mostrar el enfoque INCORRECTO de cargar un PDF completo y enviarlo todo al LLM, para que entiendas por qué es necesario dividir el texto (Text Splitting).

---

## 💻 Código clave

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI

# ⚠️ ENFOQUE INCORRECTO: enviar todo el texto al LLM
loader = PyPDFLoader("quijote.pdf")
pages = loader.load()

full_text = ""
for page in pages:
    full_text += page.page_content + "\n"

# PROBLEMA: full_text puede tener MILLONES de caracteres
# Los LLMs tienen un límite de tokens (ventana de contexto)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
response = llm.invoke(f"Haz un resumen: {full_text}")  # ← Probablemente falle
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `PyPDFLoader` | `langchain-community` + `pypdf` | Cargar PDF |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |

---

## 🧠 Concepto Clave: Ventana de Contexto

> Todo LLM tiene un **límite de tokens** que puede procesar en una sola llamada. Si el texto supera ese límite, la llamada fallará o el modelo perderá información.

| Modelo | Ventana de contexto (tokens) | Aprox. palabras |
|---|---|---|
| `gpt-4o-mini` | 128.000 tokens | ~96.000 palabras |
| `gpt-4o` | 128.000 tokens | ~96.000 palabras |
| `gemini-2.5-flash` | 1.000.000 tokens | ~750.000 palabras |
| `claude-3.5-sonnet` | 200.000 tokens | ~150.000 palabras |

---

## 🧠 Por qué NO enviar el documento completo

| Problema | Descripción |
|---|---|
| **Límite de tokens** | El texto puede superar la ventana de contexto del modelo |
| **Costo elevado** | Más tokens = más dinero en llamadas a la API |
| **Calidad de respuesta** | Los LLMs pierden atención en textos muy largos |
| **Latencia alta** | Procesar más tokens tarda más tiempo |

---

## 🔄 Solución: El Pipeline RAG

```
❌ Enfoque incorrecto:
Documento completo → LLM → Respuesta
(puede fallar por límite de tokens)

✅ Enfoque correcto (RAG):
Documento → Text Splitter → Chunks
Chunks → Embeddings → Vector Store
Consulta → Retriever → Top-K chunks relevantes
Top-K chunks + Consulta → LLM → Respuesta
```

---

## 📝 Conceptos Aprendidos

- **Ventana de contexto:** Límite de tokens que un LLM puede procesar en una llamada
- **Token:** Unidad de texto (aproximadamente 4 caracteres o 0.75 palabras)
- **Por qué RAG:** El splitting y retrieval permiten trabajar con documentos de cualquier tamaño
- **Costo de tokens:** Cada token enviado/recibido tiene un costo en las APIs comerciales

---

## ⚠️ Notas y Recomendaciones

> [!NOTE]
> Los modelos modernos como Gemini 2.5 Pro tienen contextos de 1M tokens, lo que reduce el problema para documentos medianos. Sin embargo, RAG sigue siendo más eficiente y económico para documentos muy largos.

> [!TIP]
> La solución correcta se muestra en el siguiente archivo: dividir el documento en chunks con `RecursiveCharacterTextSplitter`.

---

## 🔗 Relaciones

- Anterior → [[Tema3-02 Google Drive Loader]]
- Siguiente → [[Tema3-04 Text Splitter Parte 2]] ← la solución
- Concepto → [[Glosario RAG y LLM#Ventana de Contexto]]
- Concepto → [[Glosario RAG y LLM#RAG]]
