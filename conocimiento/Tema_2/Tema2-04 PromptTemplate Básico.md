# Tema2-04 — PromptTemplate Básico

**Archivo:** `Tema_2/4.prompt_templates.py`  
**Nivel:** 🟢 Principiante  
**Tema:** Plantillas de texto con variables dinámicas  

---

## 📖 ¿Qué hace este archivo?

Introduce el concepto de plantillas de prompts: crear un formato reutilizable con variables `{variable}` que se rellenan después. Muestra cómo probar la plantilla antes de enviarla a un LLM.

---

## 💻 Código clave

```python
from langchain_core.prompts import PromptTemplate

template = "Eres un experto en marketing. Sugiere un slogan para: {producto}"

prompt = PromptTemplate(
    template=template,
    input_variables=["producto"]
)

# Probar la plantilla ANTES de enviar al LLM
prompt_completo = prompt.format(producto="Cafe organico")
print(prompt_completo)
# → "Eres un experto en marketing. Sugiere un slogan para: Cafe organico"
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `PromptTemplate` | `langchain-core` | Plantillas de texto simples con variables |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `PromptTemplate` | Clase | Plantilla de texto para prompts simples (una sola cadena) |
| `template` | Parámetro | El texto con `{variables}` entre llaves |
| `input_variables` | Parámetro | Lista de nombres de variables esperadas |
| `.format(var=valor)` | Método | Rellena las variables y retorna el texto completo |
| `.invoke(dict)` | Método | Como `.format()` pero retorna un objeto Message |

---

## 🔄 Tipos de PromptTemplate en LangChain

```
PromptTemplate          → Plantilla de texto simple (una cadena)
ChatPromptTemplate      → Plantilla de múltiples mensajes con roles
MessagesPlaceholder     → Inserta una lista de mensajes en una posición
FewShotPromptTemplate   → Plantilla con ejemplos (few-shot learning)
```

---

## 🔄 Flujo de Ejecución

```
PromptTemplate(template, input_variables)
    ↓
.format(producto="Cafe organico")
    ↓
str: texto completo listo para enviar al LLM
```

---

## 📝 Conceptos Aprendidos

- **Plantilla:** Formato reutilizable con variables entre `{llaves}`
- **`input_variables`:** Declaración explícita de qué variables acepta la plantilla
- **`.format()`:** Prueba la plantilla antes de enviar al LLM (debugging útil)
- **Reutilización:** La misma plantilla sirve para diferentes productos/entradas

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Siempre prueba tu prompt con `.format()` antes de enviarlo al LLM. Así ves exactamente qué texto recibe el modelo.

> [!NOTE]
> `PromptTemplate` sirve para prompts de texto simple. Para conversaciones multi-mensaje usa `ChatPromptTemplate` (ver [[Tema2-05 ChatPromptTemplate]]).

> [!TIP]
> Alternativa moderna: puedes crear plantillas directamente desde strings con `PromptTemplate.from_template("texto {var}")` sin especificar `input_variables`.

---

## 🔗 Relaciones

- Anterior → [[Tema2-03 Runnables por Lotes]]
- Siguiente → [[Tema2-05 ChatPromptTemplate]]
- Comparación → [[Tema2-05 ChatPromptTemplate]] (multi-mensaje)
- Uso avanzado → [[Tema2-07 Plantilla Especializada por Rol]]
