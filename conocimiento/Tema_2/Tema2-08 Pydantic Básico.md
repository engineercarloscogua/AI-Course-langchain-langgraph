# Tema2-08 — Pydantic Básico (sin LLM)

**Archivo:** `Tema_2/8.output_parsers.py`  
**Nivel:** 🟢 Principiante  
**Tema:** BaseModel de Pydantic para validación de datos  

---

## 📖 ¿Qué hace este archivo?

Introduce Pydantic **independientemente de LangChain**, mostrando su función principal: crear modelos de datos que validan y convierten tipos automáticamente. Es la base conceptual para entender `with_structured_output()`.

> ⚠️ El nombre del archivo es `8.output_parsers.py` pero el contenido es sobre Pydantic básico, no sobre Output Parsers de LangChain.

---

## 💻 Código clave

```python
from pydantic import BaseModel

class Usuario(BaseModel):
    id: int          # Pydantic convertirá "123" → 123 automáticamente
    nombre: str
    activo: bool = True  # Valor por defecto

data = {"id": "123", "nombre": "Ana"}  # id es string, pero Pydantic lo convierte
usuario = Usuario(**data)

print(usuario.model_dump_json())
# → '{"id":123,"nombre":"Ana","activo":true}'
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `BaseModel` | `pydantic` | Clase base para modelos de datos con validación |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `BaseModel` | Clase base | Habilita validación automática de tipos |
| `id: int` | Anotación de tipo | Pydantic coerciona el valor al tipo declarado |
| `activo: bool = True` | Campo con default | Si no se provee, usa el valor por defecto |
| `Usuario(**data)` | Constructor | Desempaqueta el diccionario y valida cada campo |
| `.model_dump_json()` | Método | Serializa el objeto a JSON string |
| `.model_dump()` | Método | Serializa el objeto a diccionario Python |

---

## 🧠 Concepto Clave: Coerción de Tipos

> Pydantic intenta convertir automáticamente los valores al tipo declarado.

```python
data = {"id": "123"}  # id es str
usuario = Usuario(**data)
print(type(usuario.id))  # → <class 'int'>  (convertido de str a int)
```

---

## 🔄 Evolución de Pydantic en LangChain

| Contexto | Pydantic v1 (antiguo) | Pydantic v2 (actual) |
|---|---|---|
| Serializar a dict | `.dict()` | `.model_dump()` |
| Serializar a JSON | `.json()` | `.model_dump_json()` |
| Validar datos | `.validate()` | `.model_validate()` |

> [!WARNING]
> Los métodos `.dict()` y `.json()` están **deprecados** en Pydantic v2. Usa `.model_dump()` y `.model_dump_json()`.

---

## 📝 Conceptos Aprendidos

- **Pydantic:** Librería de validación y serialización de datos para Python
- **BaseModel:** La clase que hace que un modelo tenga validación automática
- **Coerción de tipos:** Pydantic convierte automáticamente los tipos cuando es posible
- **Valores por defecto:** Los campos sin valor en los datos usan el default definido

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Pydantic es fundamental en LangChain moderno. Todos los modelos de salida estructurada se definen como clases Pydantic.

> [!NOTE]
> Este archivo es un ejercicio de comprensión. En el contexto de LangChain, Pydantic se usa principalmente junto a `with_structured_output()` para forzar al LLM a responder en un formato específico.

---

## 🔗 Relaciones

- Anterior → [[Tema2-07 Plantilla Especializada por Rol]]
- Siguiente → [[Tema2-09 Structured Output con Pydantic]]
- Uso avanzado → [[Tema2-10 Pydantic Avanzado con Keywords]]
- Uso en proyecto → [[Tema2-11 Proyecto CV Analyzer]]
- Ver deprecaciones → [[Librerías Deprecadas y Alternativas#Pydantic]]
