# Tema2-09 — Structured Output con Pydantic y LangChain

**Archivo:** `Tema_2/9.output_parsers_pydantic.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Forzar al LLM a responder con estructura Pydantic  

---

## 📖 ¿Qué hace este archivo?

Muestra cómo usar `with_structured_output()` para hacer que el LLM devuelva **directamente un objeto Pydantic** en lugar de texto libre. LangChain genera automáticamente las instrucciones especiales para el modelo.

---

## 💻 Código clave

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import Literal

# 1. Definir la estructura deseada
class AnalisisTexto(BaseModel):
    resumen: str = Field(description="Resumen breve del texto.")
    sentimiento: Literal["Positivo", "Negativo", "Neutro"] = Field(
        description="Sentimiento identificado en el texto."
    )

# 2. Crear el LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3. Configurar salida estructurada
structured_llm = llm.with_structured_output(AnalisisTexto)

# 4. Invocar — el resultado ya es un objeto Python, no texto
resultado = structured_llm.invoke("Analiza este texto: Me encantó la película...")

print(resultado.resumen)       # → str
print(resultado.sentimiento)   # → "Positivo" | "Negativo" | "Neutro"
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `BaseModel, Field` | `pydantic` | Define la estructura de salida |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |
| `Literal` | `typing` (stdlib) | Restringe valores a opciones específicas |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `BaseModel` | Clase base Pydantic | Define la estructura de salida |
| `Field(description="...")` | Función Pydantic | Agrega descripción/metadata a un campo |
| `Literal["A", "B", "C"]` | Tipo Python | Restringe el campo a valores específicos |
| `llm.with_structured_output(Clase)` | Método LangChain | Configura el LLM para devolver un objeto Pydantic |
| `structured_llm.invoke(prompt)` | Método | Retorna directamente un objeto `AnalisisTexto` |
| `resultado.resumen` | Atributo | Acceso directo al campo del modelo |

---

## 🔄 Sin vs Con structured_output

```python
# SIN structured_output: texto libre, hay que parsear manualmente
llm = ChatOpenAI(model="gpt-4o-mini")
resp = llm.invoke("Analiza el texto y devuelve JSON...")
# resp.content = '{"resumen": "...", "sentimiento": "..."}'
# Hay que hacer json.loads() y validar manualmente

# CON structured_output: objeto Python directo
structured_llm = llm.with_structured_output(AnalisisTexto)
resp = structured_llm.invoke("Analiza el texto...")
# resp ya ES un AnalisisTexto, con validación automática
```

---

## 🧠 Concepto Clave: `Literal` de typing

> `Literal` restringe los valores que puede tomar un campo. Es como un enum, pero más simple. El LLM solo puede elegir entre los valores declarados.

```python
sentimiento: Literal["Positivo", "Negativo", "Neutro"]
# Si el LLM intenta devolver "neutral" (sin tilde) → error de validación Pydantic
```

---

## 📝 Conceptos Aprendidos

- **`with_structured_output()`:** El método más moderno y limpio para obtener datos estructurados del LLM
- **`Field(description=...)`:** La descripción ayuda al LLM a entender qué debe poner en cada campo
- **`Literal`:** Fuerza al LLM a elegir entre opciones predefinidas
- **Output Typing:** Recibir objetos Python tipados en lugar de strings

---

## ⚠️ Notas y Recomendaciones

> [!IMPORTANT]
> `with_structured_output()` es la forma **recomendada y moderna** de obtener datos estructurados. Reemplaza a los métodos antiguos como `PydanticOutputParser` + instrucciones manuales en el prompt.

> [!TIP]
> Siempre usa `Field(description="...")` para dar contexto al LLM sobre qué debe poner en cada campo. Sin la descripción, el LLM puede malinterpretar el campo.

> [!TIP]
> Usa `temperature=0` para tareas de clasificación/extracción. Las respuestas más deterministas son más fiables cuando la estructura importa.

---

## 🔗 Relaciones

- Anterior → [[Tema2-08 Pydantic Básico]]
- Siguiente → [[Tema2-10 Pydantic Avanzado con Keywords]]
- Uso en proyecto → [[Tema2-11 Proyecto CV Analyzer]]
- Comparación → [[Librerías Deprecadas y Alternativas#PydanticOutputParser]]
