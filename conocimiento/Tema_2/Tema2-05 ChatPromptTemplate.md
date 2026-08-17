# Tema2-05 — ChatPromptTemplate

**Archivo:** `Tema_2/5.chat_prompt_template.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Plantillas con múltiples roles (system/human/assistant)  

---

## 📖 ¿Qué hace este archivo?

Introduce `ChatPromptTemplate`, que permite definir una **lista de mensajes** con diferentes roles. Es más expresivo que `PromptTemplate` porque permite darle al LLM instrucciones de sistema además de la pregunta del usuario.

---

## 💻 Código clave

```python
from langchain_core.prompts import ChatPromptTemplate

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un traductor del español al inglés y eres muy preciso"),
    ("human", "{texto}")
])

# Invocar directamente con variables
mensajes = chat_prompt.invoke({"texto": "Hola, adoro salir de fiesta los domingos"})
respuesta = chat_model.invoke(mensajes)
print(respuesta.content)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatPromptTemplate` | `langchain-core` | Plantilla con múltiples roles |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `ChatPromptTemplate` | Clase | Plantilla de mensajes multi-rol |
| `.from_messages(lista)` | Método de clase | Crea plantilla desde lista de tuplas `(rol, texto)` |
| `("system", "texto")` | Tupla | Mensaje de sistema (instrucciones al LLM) |
| `("human", "{var}")` | Tupla | Mensaje del usuario con variable |
| `("assistant", "texto")` | Tupla | Mensaje de ejemplo de la IA (para few-shot) |
| `.invoke(dict)` | Método | Rellena variables y retorna lista de Messages |
| `.format_messages(dict)` | Método | Alternativa a invoke, retorna lista de Messages |

---

## 🔄 Roles en Mensajes de Chat

| Rol (tupla) | Tipo de objeto | Función |
|---|---|---|
| `"system"` | `SystemMessage` | Define comportamiento y personalidad del LLM |
| `"human"` | `HumanMessage` | Pregunta o entrada del usuario |
| `"assistant"` | `AIMessage` | Respuesta de ejemplo de la IA (few-shot) |

---

## 🔄 Flujo de Ejecución

```
ChatPromptTemplate.from_messages([
    ("system", "instrucciones"),
    ("human", "{texto}")
])
    ↓
.invoke({"texto": "Hola mundo"})
    ↓
[SystemMessage("instrucciones"), HumanMessage("Hola mundo")]
    ↓
chat_model.invoke(mensajes)
    ↓
AIMessage con traducción
```

---

## 🆚 PromptTemplate vs ChatPromptTemplate

| Aspecto | `PromptTemplate` | `ChatPromptTemplate` |
|---|---|---|
| Estructura | Una cadena de texto | Lista de mensajes con roles |
| Uso | Prompts simples, texto plano | Chatbots, conversaciones |
| Roles | No | Sí (system, human, assistant) |
| Historial | No directamente | Sí, con MessagesPlaceholder |

---

## 📝 Conceptos Aprendidos

- **Prompt multi-rol:** Combinar instrucciones del sistema con la pregunta del usuario
- **`from_messages()`:** Forma declarativa de definir la estructura de la conversación
- **System prompt:** Define la "personalidad" e instrucciones del LLM sin que el usuario las vea

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> El system prompt es la forma más efectiva de personalizar el comportamiento del LLM. Siempre úsalo para definir el rol y las restricciones del asistente.

> [!NOTE]
> `ChatPromptTemplate` es el tipo de plantilla más usado en aplicaciones reales con LangChain. `PromptTemplate` es más limitado y es solo para casos de texto simple.

---

## 🔗 Relaciones

- Anterior → [[Tema2-04 PromptTemplate Básico]]
- Siguiente → [[Tema2-06 MessagesPlaceholder]]
- Uso en proyecto real → [[Tema2-11 Proyecto CV Analyzer]]
- Variante avanzada → [[Tema2-07 Plantilla Especializada por Rol]]
