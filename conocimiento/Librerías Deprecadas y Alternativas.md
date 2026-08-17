# Librerías Deprecadas y Alternativas

> ⚠️ Todo lo que deberías EVITAR y qué usar en su lugar. Basado en el análisis real del código del proyecto.

---

## 🔴 Casos de Deprecación encontrados en el proyecto

### 1. PyPDF2 → pypdf

| Estado | Descripción |
|---|---|
| ❌ Deprecado | `PyPDF2` (desde diciembre 2022) |
| ✅ Actual | `pypdf` |

**En el proyecto:** `pdf_processor.py` ya hace la migración correcta.

```python
# ❌ ANTES (deprecado — no instalar)
import PyPDF2
pdf_reader = PyPDF2.PdfReader(file)

# ✅ AHORA (correcto)
from pypdf import PdfReader
pdf_reader = PdfReader(file)
```

> El proyecto `pdf_processor.py` en `cv_analyzer` ya usa `pypdf` correctamente. El comentario en el código lo documenta explícitamente.

---

### 2. text-embedding-ada-002 → text-embedding-3-*

| Estado | Descripción |
|---|---|
| ⚠️ Obsoleto | `text-embedding-ada-002` |
| ✅ Actual | `text-embedding-3-small` o `text-embedding-3-large` |

```python
# ⚠️ OBSOLETO (funciona pero es peor y más caro relativamente)
OpenAIEmbeddings(model="text-embedding-ada-002")

# ✅ RECOMENDADO: balance costo/calidad
OpenAIEmbeddings(model="text-embedding-3-small")

# ✅ MEJOR CALIDAD (usado en el curso)
OpenAIEmbeddings(model="text-embedding-3-large")
```

---

### 3. langchain_classic → langchain

| Estado | Descripción |
|---|---|
| ❌ No existe / Incorrecto | `from langchain_classic.retrievers.multi_query import MultiQueryRetriever` |
| ✅ Correcto | `from langchain.retrievers.multi_query import MultiQueryRetriever` |

**En el proyecto:** `8-multy-query-retriever.py` tiene este import incorrecto.

```python
# ❌ INCORRECTO (como está en el archivo 8)
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

# ✅ CORRECTO
from langchain.retrievers.multi_query import MultiQueryRetriever
```

---

### 4. Pydantic v1 → Pydantic v2

| Estado | Descripción |
|---|---|
| ⚠️ Deprecado | Métodos de Pydantic v1 |
| ✅ Actual | Métodos de Pydantic v2 |

```python
# ❌ DEPRECADO (Pydantic v1)
objeto.dict()          # → usar .model_dump()
objeto.json()          # → usar .model_dump_json()
objeto.schema()        # → usar .model_json_schema()
objeto.parse_obj(data) # → usar .model_validate(data)

# ✅ ACTUAL (Pydantic v2)
objeto.model_dump()
objeto.model_dump_json()
objeto.model_json_schema()
AnalisisTexto.model_validate(data)
```

> El proyecto **ya usa la sintaxis correcta de Pydantic v2**: `model_dump_json()` en los archivos `8.output_parsers.py` y `10.pydantic.py`.

---

### 5. PydanticOutputParser → with_structured_output()

| Estado | Descripción |
|---|---|
| ⚠️ Legado | `PydanticOutputParser` + instrucciones manuales en el prompt |
| ✅ Moderno | `llm.with_structured_output(MiClase)` |

```python
# ❌ ENFOQUE ANTIGUO (más verboso, menos confiable)
from langchain.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=MiClase)
prompt = PromptTemplate(
    template="... {format_instructions}",
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
chain = prompt | llm | parser

# ✅ ENFOQUE MODERNO (más limpio, más confiable)
structured_llm = llm.with_structured_output(MiClase)
resultado = structured_llm.invoke(prompt_texto)
```

> El proyecto **ya usa el enfoque moderno** `with_structured_output()` en los archivos 9, 10 y cv_analyzer.

---

### 6. OpenAIWhisperParser — Import innecesario

| Estado | Descripción |
|---|---|
| ⚠️ Import sobrante | `from langchain_community.document_loaders.parsers import OpenAIWhisperParser` en `5-embeding_langchain.py` |

```python
# ⚠️ SOBRANTE en el archivo 5-embeding_langchain.py
# Esta importación no se usa. OpenAIWhisperParser es para transcripción de audio, no para embeddings.
from langchain_community.document_loaders.parsers import OpenAIWhisperParser  # ← borrar
```

---

### 7. ChatPromptTemplate desde langchain_community → langchain_core

| Estado | Descripción |
|---|---|
| ⚠️ Deprecado | Importar prompts desde `langchain_community` |
| ✅ Correcto | Importar desde `langchain_core.prompts` |

```python
# ❌ Camino deprecado
from langchain.prompts import ChatPromptTemplate

# ✅ Correcto (como se usa en el proyecto)
from langchain_core.prompts import ChatPromptTemplate
```

---

## 📋 Resumen Rápido

| Elemento | ❌ Evitar | ✅ Usar |
|---|---|---|
| PDF reading | `PyPDF2` | `pypdf` |
| Embeddings económicos | `text-embedding-ada-002` | `text-embedding-3-small` |
| Embeddings calidad | `text-embedding-ada-002` | `text-embedding-3-large` |
| Salida estructurada | `PydanticOutputParser` | `with_structured_output()` |
| Serialización Pydantic | `.dict()` / `.json()` | `.model_dump()` / `.model_dump_json()` |
| Multi-Query Retriever | `langchain_classic` | `langchain.retrievers.multi_query` |
| Prompts | `langchain.prompts` | `langchain_core.prompts` |

---

## 🔗 Relaciones

- Dependencias completas → [[Librerías y Dependencias]]
- Buenas prácticas → [[Recomendaciones y Buenas Prácticas]]
- Bug en archivo 8 → [[Tema3-08 Multi-Query Retriever]]
- Bug en cv_evaluator → [[Tema2-11 Proyecto CV Analyzer]]
