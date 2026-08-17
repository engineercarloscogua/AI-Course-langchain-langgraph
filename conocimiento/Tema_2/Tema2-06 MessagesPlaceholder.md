# Tema2-06 — MessagesPlaceholder (Historial en Plantillas)

**Archivo:** `Tema_2/6.message_placeholder.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Inyectar historial de conversación dentro de una plantilla  

---

## 📖 ¿Qué hace este archivo?

Muestra cómo insertar un **historial de mensajes** (lista de `HumanMessage` y `AIMessage`) en una posición específica dentro de un `ChatPromptTemplate` usando `MessagesPlaceholder`. Es el mecanismo central para que los chatbots tengan memoria de contexto.

---

## 💻 Código clave

```python
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente útil que mantiene el contexto"),
    MessagesPlaceholder(variable_name="historial"),  # ← aquí van los mensajes previos
    ("human", "Usuario {pregunta_actual}")
])

historial = [
    HumanMessage(content="¿Cuál es la capital de Francia?"),
    AIMessage(content="La capital de Francia es París"),
]

mensajes = chat_prompt.format_messages(
    historial=historial,
    pregunta_actual="¿Cuántos habitantes tiene?"
)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `HumanMessage` | `langchain-core` | Mensaje del usuario en el historial |
| `AIMessage` | `langchain-core` | Mensaje de la IA en el historial |
| `ChatPromptTemplate` | `langchain-core` | Plantilla de mensajes |
| `MessagesPlaceholder` | `langchain-core` | Posición reservada para lista de mensajes |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `MessagesPlaceholder(variable_name="historial")` | Clase | Marcador de posición para una lista de mensajes |
| `variable_name` | Parámetro | Nombre de la variable que contendrá los mensajes |
| `.format_messages(historial=lista, ...)` | Método | Rellena variables y expande el placeholder |

---

## 🔄 Cómo funciona el Placeholder

```
Plantilla definida:
[
  SystemMessage("Eres un asistente"),
  MessagesPlaceholder("historial"),     ← marcador
  HumanMessage("Pregunta: {pregunta_actual}")
]

Al invocar con historial=[msg1, msg2]:
[
  SystemMessage("Eres un asistente"),
  HumanMessage("¿Capital de Francia?"),  ← expandido
  AIMessage("París"),                    ← expandido
  HumanMessage("Pregunta: ¿cuántos habitantes?")
]
```

---

## 🧠 Concepto Clave: Memoria de Contexto

> El LLM no tiene memoria entre llamadas. La "memoria" es simplemente enviarle todo el historial de la conversación en cada nueva petición.

```python
# Patrón estándar con historial:
mensajes_acumulados = []

# Por cada turno:
mensajes_acumulados.append(HumanMessage(content=nueva_pregunta))
respuesta = llm.invoke(mensajes_acumulados)
mensajes_acumulados.append(respuesta)
```

---

## 📝 Conceptos Aprendidos

- **MessagesPlaceholder:** Reservar un espacio en la plantilla para insertar mensajes dinámicamente
- **Contexto de conversación:** El LLM necesita toda la historia para responder con contexto
- **Simulación de historial:** Útil para probar el sistema con conversaciones predefinidas

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> En el proyecto `str_chat_mejorado.py` del Tema 1, el historial se pasa como variable al `PromptTemplate`. `MessagesPlaceholder` es una alternativa más estructurada y compatible con `ChatPromptTemplate`.

> [!NOTE]
> Para gestión avanzada de memoria (limitar tokens, resumir conversaciones antiguas), usa `ConversationBufferMemory`, `ConversationSummaryMemory` o `ConversationTokenBufferMemory` de `langchain.memory`.

> [!WARNING]
> Cuidado con historiales muy largos: consumen muchos tokens. Implementa estrategias de truncado o resumen para conversaciones extensas.

---

## 🔗 Relaciones

- Anterior → [[Tema2-05 ChatPromptTemplate]]
- Siguiente → [[Tema2-07 Plantilla Especializada por Rol]]
- Uso práctico → [[Tema1-02 Chatbot Básico Streamlit]] (historial en session_state)
- Uso práctico → [[Tema1-03 Chatbot Mejorado con LCEL]]
