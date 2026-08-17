# Tema2-03 — Runnables por Lotes (Batch)

**Archivo:** `Tema_2/3.runeables_por_lotes.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** `.batch()` — procesamiento masivo de múltiples entradas  

---

## 📖 ¿Qué hace este archivo?

Igual estructura que el archivo paralelo, pero en lugar de procesar un texto a la vez con `invoke()`, usa `batch()` para enviar **una lista completa de textos** de una sola vez. LangChain gestiona internamente el paralelismo entre entradas.

---

## 💻 Código clave

```python
textos_prueba = [
    "¡Me encanta este producto! Funciona perfectamente.",
    "El servicio fue terrible, nadie me ayudó.",
    "El clima está nublado hoy."
]

# batch(): procesa todos los textos a la vez
resultado = chain.batch(textos_prueba)
print(resultado)  # Lista de resultados, uno por entrada
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |
| `RunnableLambda` | `langchain-core` | Envuelve función como Runnable |
| `RunnableParallel` | `langchain-core` | Ejecución paralela de ramas |
| `json` | stdlib | Parsear JSON |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `chain.batch(lista)` | Método | Procesa una lista de entradas en lote |

---

## 🔄 Flujo de Ejecución

```
[texto1, texto2, texto3]  ← lista completa
    ↓
chain.batch()  ← procesa todos en paralelo
  ├── chain(texto1): preprocessor → parallel → merger
  ├── chain(texto2): preprocessor → parallel → merger
  └── chain(texto3): preprocessor → parallel → merger
    ↓
[resultado1, resultado2, resultado3]
```

---

## 🧠 Concepto Clave: invoke vs batch vs stream

| Método | Input | Output | Cuándo usar |
|---|---|---|---|
| `.invoke(x)` | Un elemento | Un resultado | Procesamiento unitario |
| `.stream(x)` | Un elemento | Iterador de chunks | UI en tiempo real |
| `.batch([x1, x2])` | Lista de elementos | Lista de resultados | Procesamiento masivo |
| `.ainvoke(x)` | Un elemento | Coroutine | Código asíncrono (async) |
| `.abatch([x1, x2])` | Lista | Lista async | Masivo + async |

---

## 📝 Conceptos Aprendidos

- **`.batch()`:** Enviar múltiples entradas de una sola vez para mayor eficiencia
- **Lote vs loop:** `chain.batch(lista)` es más eficiente que un `for` con `invoke()`
- **Mismo resultado:** El output de batch es equivalente a llamar invoke N veces, pero más rápido

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Usa `batch()` cuando tengas que procesar 10+ textos. LangChain gestiona un pool de hilos internamente para maximizar el throughput.

> [!NOTE]
> Puedes controlar la concurrencia con `max_concurrency`: `chain.batch(lista, config={"max_concurrency": 5})`

---

## 🔗 Relaciones

- Anterior → [[Tema2-02 Runnables en Paralelo]]
- Siguiente → [[Tema2-04 PromptTemplate Básico]]
- Referencia → [[Clases y Funciones Clave#invoke vs stream vs batch]]
