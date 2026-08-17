# Tema1-01 — Hello World con LLM Gemini

**Archivo:** `Tema_1/hello_world.py`  
**Nivel:** 🟢 Principiante  
**Tema:** Primera invocación directa a un LLM  

---

## 📖 ¿Qué hace este archivo?

Es el ejemplo más básico posible: crear una instancia del modelo Gemini de Google y hacerle una pregunta directa, sin interfaz gráfica ni cadenas.

## 💻 Código clave

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
respuesta = llm.invoke("Quien es el presidente de colombia en 2026?")
print(respuesta.content)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatGoogleGenerativeAI` | `langchain-google-genai` | Conectar con modelos Gemini de Google |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `ChatGoogleGenerativeAI` | Clase | Wrapper de LangChain para Google Gemini |
| `.invoke(prompt)` | Método | Envía el texto al LLM y retorna una respuesta |
| `respuesta.content` | Atributo | Texto plano de la respuesta del modelo |
| `temperature` | Parámetro | 0.0 = determinístico, 1.0 = creativo |

---

## 🔄 Flujo de Ejecución

```
prompt (str)
    ↓
llm.invoke()
    ↓
AIMessage (objeto)
    ↓
.content → texto de respuesta
```

---

## 📝 Conceptos Aprendidos

- **LLM (Large Language Model):** Modelo de lenguaje que genera texto
- **`invoke()`:** Método universal de LangChain para ejecutar cualquier componente
- **`temperature`:** Controla la "creatividad" del modelo
- **`gemini-2.5-flash`:** Modelo rápido y económico de Google DeepMind

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Para que funcione se necesita la variable de entorno `GOOGLE_API_KEY` configurada.

> [!NOTE]
> Este archivo usa Gemini (Google) mientras los otros archivos del curso usan OpenAI. Son intercambiables en LangChain gracias a la interfaz común `ChatModel`.

---

## 🔗 Relaciones

- Siguiente → [[Tema1-02 Chatbot Básico Streamlit]]
- Ver también → [[Librerías y Dependencias]]
- Concepto clave → [[Glosario RAG y LLM#LLM]]
