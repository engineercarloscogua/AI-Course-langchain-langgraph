# Tema2-01 — Runnables Orquestados por Función

**Archivo:** `Tema_2/1.runeables_orquestadoporfuncion.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** RunnableLambda y función orquestadora secuencial  

---

## 📖 ¿Qué hace este archivo?

Muestra cómo convertir funciones Python normales en componentes de LangChain usando `RunnableLambda`, y cómo coordinar múltiples llamadas al LLM con una **función orquestadora** que controla el flujo.

---

## 💻 Código clave

```python
from langchain_core.runnables import RunnableLambda

# Convertir función normal en Runnable
preprocessor = RunnableLambda(preprocess_text)
process = RunnableLambda(process_one)

# Cadena: texto → preprocesado → procesado
chain = preprocessor | process
resultado = chain.invoke("texto de prueba")
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |
| `RunnableLambda` | `langchain-core` | Convierte función Python en Runnable |
| `json` | stdlib | Parsear respuestas JSON del LLM |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `RunnableLambda(fn)` | Clase | Envuelve una función Python como componente LCEL |
| `preprocess_text(text)` | Función | Limpia y trunca el texto (max 500 chars) |
| `generate_summary(text)` | Función | Llama al LLM para resumir texto |
| `analyze_sentiment(text)` | Función | Llama al LLM para analizar sentimiento |
| `merge_results(data)` | Función | Une resumen y sentimiento en un diccionario |
| `process_one(text)` | Función | **Orquestadora:** ejecuta resumen → sentimiento → merge |
| `json.loads(content)` | Función | Convierte string JSON a diccionario Python |
| `chain.invoke(texto)` | Método | Ejecuta la cadena completa con una entrada |

---

## 🔄 Flujo de Ejecución

```
texto_entrada
    ↓
preprocess_text()  → limpia y trunca
    ↓
process_one()  ← función orquestadora secuencial
  ├── generate_summary() → llama LLM #1
  ├── analyze_sentiment() → llama LLM #2
  └── merge_results() → combina resultados
    ↓
{resumen, sentimiento, razon}
```

---

## 🧠 Concepto Clave: RunnableLambda

> Permite que cualquier función Python se comporte como un componente LangChain compatible con el operador `|` y los métodos `.invoke()`, `.stream()`, `.batch()`.

```python
# Sin RunnableLambda: no se puede encadenar con |
def mi_funcion(x): return x.upper()

# Con RunnableLambda: sí se puede encadenar
mi_runnable = RunnableLambda(mi_funcion)
cadena = mi_runnable | chat_model
```

---

## 🆚 Orquestado vs Paralelo

| Característica | Orquestado (este archivo) | Paralelo (archivo 2) |
|---|---|---|
| Ejecución | Secuencial | Concurrente |
| Tiempo total | Suma de tiempos | Tiempo del más lento |
| Complejidad | Función Python | RunnableParallel |
| Uso | Cuando un paso depende del anterior | Cuando los pasos son independientes |

---

## 📝 Conceptos Aprendidos

- **RunnableLambda:** Hacer cualquier función compatible con LCEL
- **Función orquestadora:** Controlar el orden y flujo de llamadas al LLM
- **JSON parsing:** El LLM puede devolver JSON si el prompt lo solicita explícitamente
- **Manejo de errores:** `json.JSONDecodeError` cuando el LLM no devuelve JSON válido

---

## ⚠️ Notas y Recomendaciones

> [!NOTE]
> En este archivo se hacen **2 llamadas separadas** al LLM (resumen + sentimiento) de forma secuencial. Esto es más lento que el enfoque paralelo del siguiente archivo.

> [!TIP]
> Para JSONs del LLM, usa el parámetro `method="json_mode"` en `with_structured_output()` en lugar de parsear manualmente. Más robusto y moderno.

---

## 🔗 Relaciones

- Anterior → [[Tema1-03 Chatbot Mejorado con LCEL]]
- Siguiente → [[Tema2-02 Runnables en Paralelo]]
- Complemento → [[Tema2-03 Runnables por Lotes]]
- Concepto LCEL → [[Clases y Funciones Clave#LCEL]]
