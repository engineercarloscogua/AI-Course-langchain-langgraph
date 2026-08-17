# Tema1-02 — Chatbot Básico con Streamlit y OpenAI

**Archivo:** `Tema_1/str_chat.py`  
**Nivel:** 🟢 Principiante-Intermedio  
**Tema:** Interfaz de chat con historial usando session_state  

---

## 📖 ¿Qué hace este archivo?

Construye un chatbot funcional con interfaz web usando Streamlit. Permite conversaciones con contexto (la IA recuerda mensajes anteriores) gracias a `st.session_state`.

---

## 💻 Código clave

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import streamlit as st

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# Inicializar historial en session_state
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Guardar y mostrar mensaje
st.session_state.mensajes.append(HumanMessage(content=pregunta))
respuesta = chat_model.invoke(st.session_state.mensajes)
st.session_state.mensajes.append(respuesta)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Modelo GPT de OpenAI |
| `AIMessage` | `langchain-core` | Tipo de mensaje de la IA |
| `HumanMessage` | `langchain-core` | Tipo de mensaje del usuario |
| `SystemMessage` | `langchain-core` | Instrucciones de comportamiento |
| `streamlit` | `streamlit` | Interfaz web interactiva |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `ChatOpenAI` | Clase | Wrapper para modelos GPT de OpenAI |
| `HumanMessage(content=...)` | Clase | Envuelve el texto del usuario |
| `AIMessage(content=...)` | Clase | Envuelve la respuesta de la IA |
| `SystemMessage(content=...)` | Clase | Define el comportamiento/rol del bot |
| `st.session_state` | Objeto | Diccionario persistente entre reruns |
| `st.chat_message(role)` | Función | Muestra globo de chat (user/assistant) |
| `st.chat_input(placeholder)` | Función | Campo de entrada tipo chat |
| `st.set_page_config()` | Función | Configura título e icono de la página |
| `st.columns([1,2,1])` | Función | Divide pantalla en columnas proporcionales |
| `.invoke(messages_list)` | Método | Envía historial completo al LLM |

---

## 🔄 Flujo de Ejecución

```
Usuario escribe → st.chat_input()
    ↓
HumanMessage(content=pregunta) → append a session_state
    ↓
chat_model.invoke(session_state.mensajes)  ← envía TODO el historial
    ↓
respuesta (AIMessage) → append a session_state
    ↓
Streamlit hace rerun → muestra todos los mensajes
```

---

## 🧠 Concepto Clave: session_state

> **Problema:** Streamlit re-ejecuta el script completo en cada interacción. Las variables normales se pierden.
> **Solución:** `st.session_state` es un diccionario especial que sobrevive entre ejecuciones mientras la sesión esté activa.

```python
# Patrón estándar de inicialización
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
```

---

## 📝 Conceptos Aprendidos

- **Streamlit rerun:** El script se ejecuta de arriba a abajo en cada interacción
- **Historial de mensajes:** El LLM necesita el historial completo para mantener contexto
- **Roles en mensajes:** `system`, `human`, `assistant` organizan la conversación
- **`gpt-4o-mini`:** Modelo balanceado entre velocidad, calidad y costo

---

## ⚠️ Notas y Recomendaciones

> [!NOTE]
> Este archivo usa `invoke()` para obtener toda la respuesta de una vez. La versión mejorada usa `stream()` para mostrar la respuesta en tiempo real.

> [!TIP]
> Para ejecutar: `streamlit run str_chat.py`

> [!IMPORTANT]
> Necesita la variable de entorno `OPENAI_API_KEY` configurada.

---

## 🔗 Relaciones

- Anterior → [[Tema1-01 Hello World LLM]]
- Siguiente → [[Tema1-03 Chatbot Mejorado con LCEL]]
- Diferencia con siguiente → La versión mejorada agrega streaming, sidebar con controles y LCEL
