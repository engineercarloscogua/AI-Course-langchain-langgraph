# Tema1-03 — Chatbot Mejorado con LCEL y Streaming

**Archivo:** `Tema_1/str_chat_mejorado.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** LCEL, streaming, PromptTemplate y sidebar de configuración  

---

## 📖 ¿Qué hace este archivo?

Versión avanzada del chatbot básico. Agrega:
- **LCEL** (LangChain Expression Language) con el operador `|`
- **Streaming** en tiempo real (respuesta palabra por palabra)
- **PromptTemplate** para definir el comportamiento del bot
- **Sidebar** con controles de temperatura y selección de modelo
- **Manejo de errores** con `try-except`

---

## 💻 Código clave

```python
from langchain_core.prompts import PromptTemplate

# Plantilla con variables dinámicas
prompt_template = PromptTemplate(
    input_variables=["mensaje", "historial"],
    template="Eres Viernes. {historial}\n Responde: {mensaje}"
)

# Cadena LCEL: prompt → modelo
cadena = prompt_template | chat_model

# Streaming: muestra la respuesta fragmento por fragmento
response_placeholder = st.empty()
full_response = ""
for chunk in cadena.stream({"mensaje": pregunta, "historial": historial}):
    full_response += chunk.content
    response_placeholder.markdown(full_response + "█ ")  # cursor parpadeante
response_placeholder.markdown(full_response)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Modelo GPT de OpenAI |
| `PromptTemplate` | `langchain-core` | Plantillas de texto con variables |
| `AIMessage, HumanMessage, SystemMessage` | `langchain-core` | Tipos de mensajes |
| `streamlit` | `streamlit` | Interfaz web |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `PromptTemplate` | Clase | Define plantilla con `{variables}` |
| `input_variables` | Parámetro | Lista de variables que espera la plantilla |
| `cadena = prompt \| modelo` | Expresión LCEL | Encadena componentes con el operador pipe |
| `.stream(dict)` | Método | Retorna iterador de fragmentos (chunks) |
| `chunk.content` | Atributo | Texto del fragmento actual |
| `st.empty()` | Función | Contenedor vacío que se puede actualizar |
| `st.slider()` | Función | Control deslizable para temperatura |
| `st.selectbox()` | Función | Menú desplegable para selección de modelo |
| `with st.sidebar:` | Context manager | Todo lo indentado aparece en el panel lateral |
| `st.button()` | Función | Botón clickeable, retorna True si se presiona |
| `st.rerun()` | Función | Reinicia la ejecución del script |
| `st.error()` | Función | Muestra caja roja de error |
| `st.info()` | Función | Muestra caja azul informativa |

---

## 🔄 Flujo de Ejecución

```
Sidebar:
  - st.slider() → temperature
  - st.selectbox() → model_name
  - ChatOpenAI(model=model_name, temperature=temperature) → chat_model

Prompt:
  PromptTemplate | chat_model → cadena

Usuario escribe:
    ↓
cadena.stream({"mensaje": pregunta, "historial": historial})
    ↓
chunks en tiempo real → st.empty() se actualiza con cada chunk
    ↓
Guardar: HumanMessage + AIMessage → session_state
```

---

## 🧠 Concepto Clave: LCEL (LangChain Expression Language)

> LCEL es la forma moderna de LangChain de encadenar componentes usando el operador `|` (pipe).

```python
cadena = prompt_template | chat_model
# Es equivalente a:
# resultado = chat_model.invoke(prompt_template.format(...))
```

**Ventajas de LCEL:**
- Soporte nativo de `.stream()`, `.batch()`, `.ainvoke()`
- Composición legible y declarativa
- Trazabilidad automática con LangSmith

---

## 🧠 Concepto Clave: Streaming

| Método | Comportamiento |
|---|---|
| `.invoke()` | Espera la respuesta completa y la devuelve de una vez |
| `.stream()` | Devuelve fragmentos (chunks) en tiempo real |
| `.batch()` | Procesa una lista de entradas en paralelo |

---

## 📝 Conceptos Aprendidos

- **LCEL:** Encadenar componentes con `|` para crear pipelines declarativas
- **Streaming:** Mejora la UX mostrando la respuesta progresivamente
- **PromptTemplate:** Reutilizar formato de prompts con variables
- **Cursor parpadeante:** Simular escritura con el carácter `█`

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> `.stream()` es siempre preferible a `.invoke()` en aplicaciones con UI porque el usuario siente que la respuesta es inmediata.

> [!NOTE]
> El sidebar de Streamlit re-ejecuta el script al cambiar cualquier control, creando una nueva instancia de `ChatOpenAI` con los nuevos parámetros.

---

## 🔗 Relaciones

- Anterior → [[Tema1-02 Chatbot Básico Streamlit]]
- Siguiente → [[Tema2-01 Runnables Orquestados]]
- Concepto LCEL → ver también [[Tema2-01 Runnables Orquestados]]
- Streaming vs invoke → [[Clases y Funciones Clave#invoke vs stream]]
