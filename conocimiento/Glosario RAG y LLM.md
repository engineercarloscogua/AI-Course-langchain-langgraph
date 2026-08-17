# Glosario RAG y LLM

> Definiciones de los términos clave del dominio. Ordenados temáticamente para facilitar el estudio progresivo.

---

## 🤖 Modelos de Lenguaje

### LLM (Large Language Model)
Un modelo de inteligencia artificial entrenado en grandes cantidades de texto que puede generar, resumir, traducir y razonar sobre texto. Ejemplos: GPT-4, Gemini, Claude.

### Token
La unidad básica de texto que procesa un LLM. Aproximadamente:
- 1 token ≈ 4 caracteres en inglés
- 1 token ≈ 3 caracteres en español
- 1,000 tokens ≈ 750 palabras

### Ventana de Contexto
El número máximo de tokens que un LLM puede procesar en una sola llamada (entrada + salida). Superar este límite causa errores o pérdida de información.

### Temperature
Parámetro que controla la aleatoriedad de las respuestas del LLM:
- `0.0` = Determinístico (siempre da la misma respuesta)
- `0.5` = Balance entre predictible y variado
- `1.0` = Creativo y variable

### System Prompt
Mensaje de instrucciones que define el comportamiento, rol y restricciones del LLM antes de la conversación. El usuario no lo ve, pero el modelo sí lo sigue.

### Streaming
Técnica de entrega de la respuesta del LLM fragmento por fragmento (token por token) en tiempo real, en lugar de esperar la respuesta completa.

---

## 🔗 LangChain

### LCEL (LangChain Expression Language)
La sintaxis moderna de LangChain para construir pipelines usando el operador `|` (pipe). Permite encadenar componentes de forma declarativa.

```python
cadena = prompt | llm | parser
```

### Runnable
Cualquier componente de LangChain que tenga métodos `.invoke()`, `.stream()`, `.batch()` y `.ainvoke()`. Todos los componentes de LCEL son Runnables.

### Chain (Cadena)
Una secuencia de pasos que procesan datos en orden. En LCEL, es la combinación de Runnables con el operador `|`.

### Document
El objeto estándar de LangChain para representar un fragmento de texto con sus metadatos. Tiene `page_content` (el texto) y `metadata` (dict con source, page, etc.).

---

## 📚 RAG (Retrieval Augmented Generation)

### RAG
**Retrieval Augmented Generation** — Patrón arquitectural donde el LLM augmenta su respuesta con información recuperada de una base de conocimientos externa. Soluciona el problema de que los LLMs solo saben lo que aprendieron en el entrenamiento.

```
Usuario pregunta → Búsqueda en base de conocimiento → LLM responde con contexto
```

### Document Loader
Componente que extrae texto y metadatos de fuentes externas (PDFs, Drive, web, BD) y los convierte en objetos `Document` de LangChain.

### Chunk
Un fragmento pequeño de un documento más grande, resultado de aplicar un Text Splitter. Los chunks son la unidad de indexación en los vector stores.

### Text Splitter
Algoritmo que divide documentos largos en chunks más pequeños respetando separadores naturales del texto (párrafos, oraciones, palabras).

### Chunking
El proceso de dividir un documento en chunks usando un Text Splitter.

### chunk_size
El tamaño máximo (en caracteres o tokens) de cada chunk.

### chunk_overlap
Número de caracteres compartidos entre dos chunks consecutivos, para evitar perder contexto en los bordes.

---

## 🔢 Embeddings y Vectores

### Embedding
Representación numérica del significado semántico de un texto como un vector de números (lista de floats). Textos con significado similar tienen vectores similares (ángulo pequeño entre ellos).

### Vector
Una lista de números que representa un punto en un espacio multidimensional. Los embeddings son vectores de alta dimensión (1536 o 3072 dimensiones).

### Similitud del Coseno (Cosine Similarity)
Métrica que mide el ángulo entre dos vectores para determinar qué tan similares son semánticamente. Resultado entre -1 y 1, donde 1 = idénticos en significado.

```
cos_sim = (v1 · v2) / (|v1| × |v2|)
```

### Espacio Semántico
El espacio multidimensional donde cada texto tiene una posición (vector). Textos con significado similar están "cerca" en este espacio.

---

## 🗄️ Vector Store

### Vector Store (Almacén de Vectores)
Base de datos especializada que almacena embeddings y permite búsquedas de similitud eficientes. Es el "cerebro" del sistema RAG.

### Indexación
El proceso de convertir documentos en embeddings y almacenarlos en el vector store. Se hace UNA vez y luego se consulta muchas veces.

### Búsqueda Semántica (Similarity Search)
Búsqueda que encuentra documentos similares en significado (no en palabras exactas) usando la similitud del coseno entre vectores.

### k (en similarity_search)
Número de documentos más relevantes a retornar en una búsqueda. `k=3` retorna los 3 chunks más similares a la consulta.

---

## 🔎 Retrievers

### Retriever
Abstracción de LangChain que encapsula cualquier mecanismo de búsqueda con la interfaz `.invoke(query)` → `list[Document]`.

### Multi-Query Retriever
Técnica que usa el LLM para generar múltiples variaciones de la consulta del usuario y ejecutar varias búsquedas en el vector store, combinando los resultados únicos para mayor cobertura.

### MMR (Maximum Marginal Relevance)
Algoritmo de búsqueda que balancea relevancia con diversidad. Evita retornar múltiples chunks muy similares entre sí.

---

## 🔐 Autenticación

### OAuth2
Protocolo estándar de autorización que permite a una aplicación acceder a recursos de Google (Drive, Gmail, etc.) con los permisos del usuario, sin conocer su contraseña.

### Access Token
Credencial temporal (válida por ~1 hora) que permite hacer llamadas a la API de Google.

### Refresh Token
Token de larga vida que permite renovar el Access Token automáticamente cuando expira, sin necesidad de que el usuario vuelva a hacer login.

### Scopes (OAuth)
Permisos específicos que solicita la aplicación. `drive.readonly` = solo leer archivos de Drive.

---

## 📊 Pydantic

### BaseModel
Clase base de Pydantic que habilita la validación automática de tipos y la serialización de datos en una clase Python.

### Coerción de Tipos
Capacidad de Pydantic de convertir automáticamente los valores al tipo declarado cuando es posible (e.g., `"123"` → `123` para un campo `int`).

### with_structured_output()
Método de LangChain que configura un LLM para que devuelva directamente un objeto Pydantic en lugar de texto libre.

---

## 🔗 Relaciones

- Clases en código → [[Clases y Funciones Clave]]
- Librerías → [[Librerías y Dependencias]]
- Buenas prácticas → [[Recomendaciones y Buenas Prácticas]]
- Volver al inicio → [[🏠 INICIO - Mapa del Conocimiento]]
