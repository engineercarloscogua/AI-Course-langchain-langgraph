# Clases y Funciones Clave

> Referencia rápida de todos los elementos importantes usados en el proyecto. Busca aquí cuando quieras recordar para qué sirve algo.

---

## 🤖 Modelos LLM

| Clase | Paquete | Descripción |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Conecta con GPT-3.5, GPT-4, GPT-4o-mini |
| `ChatGoogleGenerativeAI` | `langchain-google-genai` | Conecta con Gemini 2.5 Flash/Pro |
| `OpenAIEmbeddings` | `langchain-openai` | Convierte texto en vectores numéricos |

### Parámetros de los modelos

```python
ChatOpenAI(
    model="gpt-4o-mini",   # modelo a usar
    temperature=0.0,        # 0 = determinístico, 1 = creativo
    max_tokens=None,        # límite de tokens en la respuesta
    streaming=True,         # para uso con .stream()
)
```

---

## 💬 Mensajes

| Clase | Rol | Descripción |
|---|---|---|
| `HumanMessage(content=str)` | `"human"` / `"user"` | Mensaje del usuario |
| `AIMessage(content=str)` | `"assistant"` | Respuesta de la IA |
| `SystemMessage(content=str)` | `"system"` | Instrucciones de comportamiento |

---

## 🔗 LCEL — Runnables

| Clase/Operador | Descripción |
|---|---|
| `A \| B` | Encadena A y B: salida de A → entrada de B |
| `RunnableLambda(fn)` | Convierte función Python en Runnable |
| `RunnableParallel({...})` | Ejecuta múltiples Runnables en paralelo |
| `RunnablePassthrough()` | Pasa la entrada sin modificar |

### invoke vs stream vs batch

```python
# Un elemento, respuesta completa
resultado = chain.invoke(entrada)

# Un elemento, respuesta en tiempo real (fragmentos)
for chunk in chain.stream(entrada):
    print(chunk.content, end="")

# Lista de elementos, procesamiento en lote
resultados = chain.batch([entrada1, entrada2, entrada3])

# Async
resultado = await chain.ainvoke(entrada)
```

---

## 📝 Prompts

| Clase | Descripción |
|---|---|
| `PromptTemplate` | Plantilla de texto simple con `{variables}` |
| `ChatPromptTemplate` | Plantilla de mensajes multi-rol |
| `SystemMessagePromptTemplate` | Plantilla específica para mensajes system |
| `HumanMessagePromptTemplate` | Plantilla específica para mensajes human |
| `MessagesPlaceholder(variable_name)` | Inserta una lista de mensajes en la posición definida |

### Métodos de Prompts

```python
# Crear plantilla
prompt = PromptTemplate(template="...", input_variables=["var1"])
prompt = ChatPromptTemplate.from_messages([("system", "..."), ("human", "{var}")])

# Rellenar variables
texto = prompt.format(var1="valor")                    # → str
mensajes = chat_prompt.format_messages(var="valor")    # → list[Message]
mensajes = chat_prompt.invoke({"var": "valor"})        # → ChatPromptValue
```

---

## 🔍 Output Parsers y Structured Output

| Método | Descripción |
|---|---|
| `llm.with_structured_output(MiClase)` | Configura el LLM para devolver un objeto Pydantic |
| `structured_llm.invoke(prompt)` | Retorna directamente un objeto de `MiClase` |

```python
class MiModelo(BaseModel):
    campo1: str = Field(description="Descripción clara para el LLM")
    campo2: Literal["A", "B", "C"] = Field(description="Una de estas opciones")
    lista: list[str] = Field(description="Lista de elementos")

structured_llm = llm.with_structured_output(MiModelo)
resultado = structured_llm.invoke("Tu prompt aquí")
print(resultado.campo1)  # acceso directo al campo
```

---

## 📚 Document Loaders

| Clase | Fuente | Método principal |
|---|---|---|
| `PyPDFLoader(ruta)` | PDF local | `.load()` → `list[Document]` |
| `PyPDFDirectoryLoader(carpeta)` | Carpeta de PDFs | `.load()` → `list[Document]` |
| `GoogleDriveLoader(folder_id, credentials)` | Google Drive | `.load()` → `list[Document]` |

```python
# Objeto Document
Document(
    page_content="Texto de la página...",
    metadata={"source": "archivo.pdf", "page": 0}
)
```

---

## ✂️ Text Splitters

| Clase | Descripción |
|---|---|
| `RecursiveCharacterTextSplitter` | **El más recomendado** — divide en separadores naturales |
| `CharacterTextSplitter` | Divide por un solo separador fijo |
| `TokenTextSplitter` | Divide por tokens (requiere tiktoken) |

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # máximo de caracteres por chunk
    chunk_overlap=200,     # caracteres compartidos entre chunks consecutivos
    separators=[".\n", "\n", " "]  # separadores en orden de preferencia
)
chunks = splitter.split_documents(documents)  # → list[Document]
chunks = splitter.split_text(texto_str)       # → list[str]
```

---

## 🗄️ Vector Stores

| Clase | Descripción |
|---|---|
| `Chroma.from_documents(docs, embedding, persist_directory)` | Crea e indexa una nueva BD |
| `Chroma(embedding_function, persist_directory)` | Abre una BD existente (sin re-indexar) |

```python
# Métodos de búsqueda
vectorstore.similarity_search(query, k=3)                    # → list[Document]
vectorstore.similarity_search_with_score(query, k=3)         # → list[(Document, float)]
vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})  # → Retriever
```

---

## 🔎 Retrievers

| Clase | Descripción |
|---|---|
| `vectorstore.as_retriever(...)` | Retriever básico desde vector store |
| `MultiQueryRetriever.from_llm(retriever, llm)` | Retriever que genera múltiples variaciones |

```python
# Tipos de búsqueda en as_retriever
"similarity"                    # Los K más similares
"mmr"                           # Maximum Marginal Relevance (más diverso)
"similarity_score_threshold"    # Solo los que superen un umbral
```

---

## 🎨 Streamlit (UI)

| Función | Descripción |
|---|---|
| `st.set_page_config(page_title, page_icon, layout)` | Config global de la página |
| `st.title(texto)` | Título H1 |
| `st.header(texto)` | Título H2 |
| `st.subheader(texto)` | Título H3 |
| `st.markdown(texto)` | Texto con formato Markdown |
| `st.chat_message(role)` | Globo de chat (user/assistant) |
| `st.chat_input(placeholder)` | Campo de entrada tipo chat |
| `st.empty()` | Contenedor vacío actualizable (para streaming) |
| `st.columns([1, 2, 1])` | Divide pantalla en columnas |
| `st.sidebar` | Panel lateral |
| `st.slider(label, min, max, default, step)` | Control deslizable |
| `st.selectbox(label, opciones)` | Menú desplegable |
| `st.button(label, type)` | Botón clickeable |
| `st.file_uploader(label, type)` | Subir archivos |
| `st.progress(porcentaje)` | Barra de progreso |
| `st.spinner(mensaje)` | Indicador de carga |
| `st.metric(label, value, delta)` | Métrica destacada |
| `st.success(texto)` | Caja verde |
| `st.warning(texto)` | Caja amarilla |
| `st.error(texto)` | Caja roja |
| `st.info(texto)` | Caja azul |
| `st.session_state` | Diccionario persistente entre reruns |
| `st.rerun()` | Reinicia el script desde el principio |

---

## 🔢 Pydantic v2

| Elemento | Descripción |
|---|---|
| `class Mi(BaseModel)` | Define un modelo de datos con validación |
| `field: tipo = Field(description="...")` | Campo con metadata |
| `field: Literal["A","B"]` | Campo restringido a valores específicos |
| `field: list[str]` | Campo de lista de strings |
| `ge=0, le=100` | Validación numérica (≥0 y ≤100) |
| `.model_dump()` | Serializa a dict |
| `.model_dump_json(indent=2)` | Serializa a JSON string |
| `.model_validate(data)` | Crea objeto desde dict con validación |

---

## 🔗 Relaciones

- Dependencias → [[Librerías y Dependencias]]
- Deprecadas → [[Librerías Deprecadas y Alternativas]]
- Recomendaciones → [[Recomendaciones y Buenas Prácticas]]
