# Recomendaciones y Buenas Prácticas

> Consejos prácticos para escribir código LangChain moderno, mantenible y eficiente. Basados en el análisis del proyecto.

---

## 🏗️ Arquitectura de Proyectos LangChain

### Patrón multi-módulo (como cv_analyzer)

```
mi_proyecto/
├── app.py               # Punto de entrada
├── models/
│   └── mi_modelo.py     # Clases Pydantic
├── prompts/
│   └── mis_prompts.py   # Templates de prompts
├── services/
│   └── mi_servicio.py   # Lógica de negocio + cadenas LCEL
└── ui/
    └── streamlit_ui.py  # Interfaz de usuario
```

> ✅ Separar modelos, prompts, servicios y UI hace el código más testeable y reutilizable.

---

## 🔗 LCEL: Mejores Prácticas

### Siempre usa LCEL para encadenar componentes

```python
# ❌ Imperativo (antiguo)
def mi_cadena(prompt_text):
    mensajes = prompt_template.format_messages(texto=prompt_text)
    respuesta = llm.invoke(mensajes)
    return parser.parse(respuesta.content)

# ✅ LCEL (moderno y declarativo)
cadena = prompt_template | llm | parser
resultado = cadena.invoke({"texto": prompt_text})
```

### Aprovecha el paralelismo cuando sea posible

```python
# ❌ Secuencial: suma de tiempos
resumen = resumidor.invoke(texto)
sentimiento = analizador.invoke(texto)

# ✅ Paralelo: tiempo del más lento
paralelo = RunnableParallel({
    "resumen": resumidor,
    "sentimiento": analizador
})
resultado = paralelo.invoke(texto)
```

---

## 🎯 Prompts: Mejores Prácticas

### System prompt siempre presente

```python
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en {especialidad}. Responde de forma {tono}."),
    ("human", "{pregunta}")
])
```

### Describe bien los campos en Pydantic

```python
class Analisis(BaseModel):
    # ❌ Sin descripción → el LLM puede malinterpretar
    sentimiento: str
    
    # ✅ Con descripción → el LLM sabe exactamente qué poner
    sentimiento: Literal["Positivo", "Negativo", "Neutro"] = Field(
        description="Clasificación del tono emocional: Positivo (alegría/satisfacción), "
                    "Negativo (enojo/insatisfacción), Neutro (informativo/imparcial)"
    )
```

### Siempre prueba el prompt antes de enviarlo al LLM

```python
# Ver exactamente qué texto recibe el modelo
prompt_completo = mi_prompt.format(variable="valor_de_prueba")
print(prompt_completo)
```

---

## 📊 Temperature: Guía por Caso de Uso

| temperature | Uso recomendado |
|---|---|
| `0.0` | Extracción de datos, clasificación, análisis (máxima consistencia) |
| `0.1 - 0.3` | Resúmenes, traducción, análisis de sentimiento |
| `0.5 - 0.7` | Chatbots conversacionales, asistentes generales |
| `0.8 - 1.0` | Creatividad, escritura creativa, brainstorming |

---

## 🗄️ Vector Stores en Producción

| Vector Store | Cuándo usar | Pros | Contras |
|---|---|---|---|
| **ChromaDB** | Desarrollo, prototipado | Local, simple, sin infra | No escala bien en producción |
| **FAISS** | Proyectos medianos | Muy rápido, gratuito | Solo en memoria (sin persistencia nativa) |
| **Pinecone** | Producción cloud | Escalable, gestionado | Costo mensual |
| **pgvector** | Ya usas PostgreSQL | Integrado con tu BD | Más lento que soluciones especializadas |
| **Weaviate** | Producción self-hosted | Búsqueda híbrida | Más complejo de configurar |

---

## ✂️ Text Splitting: Parámetros Óptimos por Caso

| Caso | chunk_size | chunk_overlap | separators |
|---|---|---|---|
| RAG / búsqueda semántica | 500-1500 | 100-200 | default |
| Contratos legales | 800-1200 | 150-200 | `[".\n", "\n"]` |
| Código fuente | 1500-3000 | 300 | `["\nclass ", "\ndef ", "\n"]` |
| Noticias/artículos | 300-800 | 50-100 | `["\n\n", "\n"]` |
| Resúmenes de docs | 5000-15000 | 500 | default |

---

## 🔄 Pipeline RAG Completo — Patrón recomendado

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 2. Prompt con contexto
prompt = ChatPromptTemplate.from_messages([
    ("system", "Responde usando SOLO la siguiente información:\n{contexto}"),
    ("human", "{pregunta}")
])

# 3. Cadena RAG completa
rag_chain = (
    {"contexto": retriever, "pregunta": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 4. Invocar
respuesta = rag_chain.invoke("¿Cuál es la vigencia del contrato?")
```

---

## 🔐 Seguridad: Variables de Entorno

```python
# ❌ NUNCA hardcodear API keys en el código
llm = ChatOpenAI(api_key="sk-1234567890")  # Peligroso

# ✅ Usar variables de entorno
import os
# LangChain las lee automáticamente de OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini")

# ✅ O con python-dotenv para desarrollo local
from dotenv import load_dotenv
load_dotenv()  # Lee el archivo .env
```

---

## 🐛 Manejo de Errores

```python
# ✅ Patrón recomendado para llamadas al LLM
try:
    resultado = cadena.invoke(datos)
except Exception as e:
    # Opciones:
    # 1. Retornar valor por defecto (como en cv_evaluator.py)
    # 2. Mostrar error al usuario (como en str_chat_mejorado.py)
    # 3. Reintentar con backoff exponencial
    logger.error(f"Error en llamada al LLM: {e}")
    return valor_por_defecto
```

---

## 🚀 Técnicas Avanzadas de RAG

| Técnica | Descripción | Dificultad |
|---|---|---|
| **Multi-Query Retriever** | Genera variaciones de la consulta | 🟡 Medio (ya en el curso) |
| **HyDE** | Genera documento hipotético, lo embede y busca similares | 🔴 Avanzado |
| **RAG-Fusion** | Combina múltiples queries con Reciprocal Rank Fusion | 🔴 Avanzado |
| **Contextual Compression** | Comprime los chunks recuperados antes de enviar al LLM | 🟡 Medio |
| **Self-RAG** | El LLM decide cuándo y cómo recuperar información | 🔴 Muy avanzado |
| **Adaptive RAG** | Sistema que enruta preguntas al método más apropiado | 🔴 Muy avanzado |

---

## 🔗 Relaciones

- Dependencias → [[Librerías y Dependencias]]
- Deprecadas → [[Librerías Deprecadas y Alternativas]]
- Clases → [[Clases y Funciones Clave]]
- Glosario → [[Glosario RAG y LLM]]
