# Tema2-10 — Pydantic Avanzado con Lista de Palabras Clave

**Archivo:** `Tema_2/10.pydantic.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** Pydantic con campos tipo lista y buenas prácticas  

---

## 📖 ¿Qué hace este archivo?

Amplía el uso de `with_structured_output()` con un modelo Pydantic más complejo que incluye un campo de tipo `list[str]`. También muestra el patrón `if __name__ == "__main__"` para organizar el código correctamente.

---

## 💻 Código clave

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class AnalisisTexto(BaseModel):
    resumen: str = Field(description="Resumen breve del texto")
    sentimiento: str = Field(description="Sentimiento: Positivo, Neutro o Negativo")
    palabras_clave: list[str] = Field(description="3 a 5 palabras clave principales")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
structured_llm = llm.with_structured_output(AnalisisTexto)

if __name__ == "__main__":
    resultado = structured_llm.invoke(prompt)
    print(resultado.resumen)
    print(resultado.palabras_clave)  # → ["película", "efectos", "acción"]
    print(resultado.model_dump_json(indent=2))
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `BaseModel, Field` | `pydantic` | Modelo de datos estructurado |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `list[str]` | Tipo Python | Campo de lista de strings (Python 3.9+) |
| `if __name__ == "__main__":` | Patrón Python | Ejecuta código solo cuando el archivo se corre directamente |
| `.model_dump_json(indent=2)` | Método Pydantic v2 | Serializa a JSON con indentado |
| `.model_dump()` | Método Pydantic v2 | Serializa a diccionario Python |
| `resultado.palabras_clave` | Atributo | Lista de strings directamente usable |

---

## 🆚 Diferencia con archivo 9

| Aspecto | Archivo 9 | Archivo 10 |
|---|---|---|
| Sentimiento | `Literal["Positivo","Negativo","Neutro"]` | `str` libre |
| Campos | 2 campos | 3 campos (agrega `palabras_clave`) |
| Tipo lista | No | Sí (`list[str]`) |
| Patrón `__main__` | No | Sí |
| temperature | 0 | 0.2 |

---

## 🧠 Concepto Clave: `list[str]` en Pydantic

> Pydantic soporta tipos genéricos de Python. El LLM entiende que debe devolver una lista de strings.

```python
palabras_clave: list[str] = Field(description="3 a 5 palabras clave")
# El LLM devuelve: ["película", "efectos especiales", "acción", "felicidad"]
# Pydantic valida que sea una lista de strings
```

---

## 🧠 Concepto Clave: `if __name__ == "__main__"`

> Este patrón permite que el archivo pueda ser **importado como módulo** sin ejecutar el código principal.

```python
# Cuando ejecutas directamente: python 10.pydantic.py
# → __name__ == "__main__" → entra en el if → ejecuta el código

# Cuando importas desde otro archivo: from 10 import AnalisisTexto
# → __name__ == "10" → NO entra en el if → solo importa la clase
```

---

## 📝 Conceptos Aprendidos

- **`list[str]`:** El LLM puede devolver listas nativas de Python a través de Pydantic
- **`if __name__ == "__main__"`:** Buena práctica para separar definiciones de ejecución
- **`model_dump_json(indent=2)`:** Serialización legible del modelo a JSON
- **temperature=0.2:** Ligera creatividad para tareas de extracción de palabras clave

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Usa `Literal` cuando quieras **garantizar** que el LLM elige entre opciones específicas. Usa `str` cuando cualquier valor es válido pero quieres sugerirle el formato en la descripción.

> [!TIP]
> El patrón `if __name__ == "__main__"` es una **buena práctica** que deberías usar siempre en archivos que tienen tanto definiciones de clases/funciones como código de ejecución.

> [!NOTE]
> `list[str]` requiere Python 3.9+. En versiones anteriores usa `List[str]` de `typing`.

---

## 🔗 Relaciones

- Anterior → [[Tema2-09 Structured Output con Pydantic]]
- Siguiente → [[Tema2-11 Proyecto CV Analyzer]]
- Uso en proyecto → [[Tema2-11 Proyecto CV Analyzer]] (modelo AnalisisCV más complejo)
- Serialización → [[Librerías Deprecadas y Alternativas#Pydantic v1 vs v2]]
