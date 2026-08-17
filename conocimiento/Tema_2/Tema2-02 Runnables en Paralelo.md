# Tema2-02 — Runnables en Paralelo

**Archivo:** `Tema_2/2.runeables_paralelo.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** RunnableParallel — ejecución concurrente de ramas  

---

## 📖 ¿Qué hace este archivo?

Mejora la eficiencia del archivo anterior ejecutando el resumen y el análisis de sentimiento **al mismo tiempo** (en paralelo) usando `RunnableParallel`. Ambas tareas son independientes y no necesitan el resultado de la otra para ejecutarse.

---

## 💻 Código clave

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel

# Cada función envuelta como Runnable independiente
summary_branch = RunnableLambda(generate_summary)
sentiment_branch = RunnableLambda(analyze_sentiment)

# Ejecución paralela: ambas funciones reciben el mismo input
parallel_analysis = RunnableParallel({
    "resumen": summary_branch,
    "sentimiento_data": sentiment_branch
})

# Cadena completa: preprocesar → paralelo → unir
chain = preprocessor | parallel_analysis | merger
resultado = chain.invoke("texto de prueba")
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |
| `RunnableLambda` | `langchain-core` | Envuelve función como Runnable |
| `RunnableParallel` | `langchain-core` | Ejecuta múltiples Runnables en paralelo |
| `json` | stdlib | Parsear JSON |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `RunnableParallel({...})` | Clase | Ejecuta un diccionario de Runnables en paralelo |
| `summary_branch` | RunnableLambda | Rama de resumen |
| `sentiment_branch` | RunnableLambda | Rama de sentimiento |
| `merger` | RunnableLambda | Une los resultados del paralelo |
| `chain.invoke(texto)` | Método | Ejecuta la cadena completa |

---

## 🔄 Flujo de Ejecución

```
texto_entrada
    ↓
preprocess_text()
    ↓
RunnableParallel ┬─→ generate_summary()   → "resumen"
                └─→ analyze_sentiment()  → "sentimiento_data"
    ↓
(ambas terminan → se combinan en un dict)
    ↓
merge_results({resumen, sentimiento_data})
    ↓
{resumen, sentimiento, razon}
```

---

## 🧠 Concepto Clave: RunnableParallel

> `RunnableParallel` recibe un diccionario donde cada valor es un `Runnable`. Todos reciben **el mismo input** y se ejecutan **al mismo tiempo**. El resultado es un diccionario con las salidas de cada rama.

```python
# Input: texto
# Output: {"resumen": "...", "sentimiento_data": {...}}
parallel = RunnableParallel({
    "resumen": summary_branch,        # recibe texto → devuelve str
    "sentimiento_data": sentiment_branch  # recibe texto → devuelve dict
})
```

---

## 🆚 Comparación con Orquestado

| Aspecto | Orquestado (archivo 1) | Paralelo (este archivo) |
|---|---|---|
| Llamadas al LLM | Secuenciales | Simultáneas (hilos) |
| Tiempo aprox. | T(resumen) + T(sentimiento) | max(T(resumen), T(sentimiento)) |
| Código | Función Python | RunnableParallel |
| Cuándo usar | Pasos dependientes | Pasos independientes |

---

## 📝 Conceptos Aprendidos

- **RunnableParallel:** Bifurcar la cadena en múltiples ramas independientes
- **Mismo input:** Todas las ramas de un paralelo reciben exactamente la misma entrada
- **Combinación automática:** El resultado es un dict con las salidas de todas las ramas

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Usa `RunnableParallel` siempre que tengas dos tareas independientes sobre el mismo dato. Reduce el tiempo de espera a la mitad (o más) cuando hay múltiples llamadas al LLM.

> [!NOTE]
> En Python, `RunnableParallel` usa hilos internamente (ThreadPoolExecutor). Para código async usa `.ainvoke()`.

---

## 🔗 Relaciones

- Anterior → [[Tema2-01 Runnables Orquestados]]
- Siguiente → [[Tema2-03 Runnables por Lotes]]
- Complemento → [[Clases y Funciones Clave#RunnableParallel]]
