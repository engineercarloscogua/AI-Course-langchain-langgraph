# Tema3-05 — Embeddings con OpenAI

**Archivo:** `Tema_3/5-embeding_langchain.py`  
**Nivel:** 🔴 Avanzado (concepto)  
**Tema:** Convertir texto en vectores numéricos y medir similitud semántica  

---

## 📖 ¿Qué hace este archivo?

Introduce el concepto de **embeddings** (incrustaciones): transformar texto en listas de números (vectores) que representan el significado semántico. Luego calcula la **similitud del coseno** para medir qué tan similares son dos textos.

---

## 💻 Código clave

```python
from langchain_openai import OpenAIEmbeddings
import numpy as np

# Crear el modelo de embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

texto1 = "París es un buen lugar para tener mascotas"
texto2 = "París es la capital de Francia"

# Convertir textos a vectores numéricos
vec1 = embeddings.embed_query(texto1)  # → lista de 3072 números
vec2 = embeddings.embed_query(texto2)  # → lista de 3072 números

# Calcular similitud del coseno
cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
print(f"Similitud: {cos_sim:.3f}")  # → entre 0 y 1 (más cercano a 1 = más similar)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `OpenAIEmbeddings` | `langchain-openai` | Convertir texto en vectores usando OpenAI |
| `numpy` | `numpy` | Operaciones matemáticas con vectores |

> ⚠️ El archivo importa `OpenAIWhisperParser` (una importación innecesaria/error) que no se usa en el código.

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `OpenAIEmbeddings(model="...")` | Clase | Modelo de embeddings de OpenAI |
| `.embed_query(texto)` | Método | Convierte UN texto en vector (para consultas) |
| `.embed_documents(lista_textos)` | Método | Convierte VARIOS textos en vectores (para documentos) |
| `np.dot(vec1, vec2)` | Función NumPy | Producto punto (parte del cálculo de coseno) |
| `np.linalg.norm(vec)` | Función NumPy | Norma (módulo) del vector |

---

## 🧠 Concepto Clave: ¿Qué es un Embedding?

> Un embedding es una representación numérica del significado semántico de un texto. Textos con significado similar tienen vectores similares (ángulo pequeño entre ellos).

```
"El gato duerme"       → [0.12, -0.45, 0.89, ...]  ← 3072 números
"El felino descansa"   → [0.11, -0.43, 0.91, ...]  ← similar al anterior
"La física cuántica"   → [0.67, 0.23, -0.12, ...]  ← muy diferente
```

---

## 🧠 Concepto Clave: Similitud del Coseno

> Mide el ángulo entre dos vectores. **No mide la distancia**, sino la **dirección** (significado).

```
cos_sim = (vec1 · vec2) / (|vec1| × |vec2|)

Resultado:
  1.0  → Textos idénticos en significado
  0.7  → Textos relacionados
  0.0  → Textos sin relación
 -1.0  → Textos opuestos en significado
```

---

## 📊 Modelos de Embedding disponibles

| Modelo | Dimensiones | Precio | Uso recomendado |
|---|---|---|---|
| `text-embedding-3-small` | 1536 | Barato | RAG de bajo costo |
| `text-embedding-3-large` | 3072 | Moderado | **RAG de alta calidad** (usado en el curso) |
| `text-embedding-ada-002` | 1536 | Moderado | ⚠️ Antiguo, usar `3-small` en su lugar |

---

## 🔄 Diferencia: embed_query vs embed_documents

```python
# Para la CONSULTA del usuario (una sola frase)
vec = embeddings.embed_query("¿Cuál es la capital de Francia?")

# Para los DOCUMENTOS del corpus (pueden ser muchos)
vecs = embeddings.embed_documents(["Francia", "España", "Italia"])
```

> Internamente pueden usar diferentes prompts/pesos para optimizar la búsqueda.

---

## 📝 Conceptos Aprendidos

- **Embedding:** Representación numérica del significado semántico de un texto
- **Vector:** Lista de números (`[0.12, -0.45, ...]`) de dimensión fija
- **Similitud del coseno:** Métrica de similitud basada en el ángulo entre vectores
- **Espacio semántico:** Espacio multidimensional donde textos similares están cerca

---

## ⚠️ Notas y Recomendaciones

> [!NOTE]
> El archivo importa `OpenAIWhisperParser` innecesariamente. Es un import sobrante que no se usa y puede causar confusión.

> [!TIP]
> En producción, no calcules la similitud del coseno manualmente. Los Vector Stores (ChromaDB, Pinecone, etc.) lo hacen automáticamente y de forma más eficiente.

> [!IMPORTANT]
> `text-embedding-ada-002` está **obsoleto**. Usa `text-embedding-3-small` o `text-embedding-3-large` según el balance costo/calidad que necesites.

---

## 🔗 Relaciones

- Anterior → [[Tema3-04 Text Splitter Parte 2]]
- Siguiente → [[Tema3-06 Vector Store Chroma]]
- Uso práctico → [[Tema3-06 Vector Store Chroma]] (los embeddings se usan para indexar)
- Deprecaciones → [[Librerías Deprecadas y Alternativas#text-embedding-ada-002]]
- Glosario → [[Glosario RAG y LLM#Embedding]]
