# Tema2-07 — Plantilla Especializada por Rol

**Archivo:** `Tema_2/7. plant_esp_rol.py`  
**Nivel:** 🟡 Intermedio  
**Tema:** SystemMessagePromptTemplate + HumanMessagePromptTemplate  

---

## 📖 ¿Qué hace este archivo?

Muestra una forma más explícita y granular de construir plantillas usando las clases especializadas `SystemMessagePromptTemplate` y `HumanMessagePromptTemplate`. Permite tener **múltiples variables dinámicas** tanto en el mensaje del sistema como en el del usuario.

---

## 💻 Código clave

```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# Sistema con múltiples variables
plantilla_sistema = SystemMessagePromptTemplate.from_template(
    "Eres un {rol} especializado en {especialidad}. Responde de manera {tono}"
)

# Humano con múltiples variables
plantilla_humano = HumanMessagePromptTemplate.from_template(
    "Mi pregunta sobre {tema} es: {pregunta}"
)

# Combinar en un ChatPromptTemplate
chat_prompt = ChatPromptTemplate.from_messages([
    plantilla_sistema,
    plantilla_humano
])

# Rellenar todas las variables
mensajes = chat_prompt.format_messages(
    rol="nutricionista",
    especialidad="dietas veganas",
    tono="profesional pero accesible",
    tema="proteínas vegetales",
    pregunta="¿Cuáles son las mejores fuentes de proteína para un niño de 10 años?"
)
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `ChatPromptTemplate` | `langchain-core` | Plantilla combinada |
| `SystemMessagePromptTemplate` | `langchain-core` | Plantilla específica para mensajes de sistema |
| `HumanMessagePromptTemplate` | `langchain-core` | Plantilla específica para mensajes humanos |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `SystemMessagePromptTemplate` | Clase | Crea plantilla que genera `SystemMessage` |
| `HumanMessagePromptTemplate` | Clase | Crea plantilla que genera `HumanMessage` |
| `.from_template("texto {var}")` | Método de clase | Crea la plantilla desde un string |
| `ChatPromptTemplate.from_messages(lista)` | Método de clase | Combina plantillas de distintos roles |
| `.format_messages(**vars)` | Método | Rellena todas las variables y retorna lista de Messages |

---

## 🆚 Métodos para construir ChatPromptTemplate

```python
# Método 1: Tuplas (más conciso, más común)
ChatPromptTemplate.from_messages([
    ("system", "Eres un {rol}"),
    ("human", "Pregunta: {pregunta}")
])

# Método 2: Clases especializadas (más explícito, más control)
ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("Eres un {rol}"),
    HumanMessagePromptTemplate.from_template("Pregunta: {pregunta}")
])
```

Ambos métodos producen exactamente el mismo resultado. El método 2 es útil cuando necesitas lógica adicional al construir las plantillas.

---

## 📝 Conceptos Aprendidos

- **Plantillas de sistema con variables:** El rol, especialidad y tono pueden ser dinámicos
- **Separación de responsabilidades:** Definir system y human por separado mejora la legibilidad
- **Variables múltiples:** Una sola plantilla puede tener muchas variables independientes

---

## ⚠️ Notas y Recomendaciones

> [!TIP]
> Las clases `SystemMessagePromptTemplate` y `HumanMessagePromptTemplate` son más verbosas pero más explícitas. Para la mayoría de casos, la sintaxis de tuplas es suficiente y más limpia.

> [!NOTE]
> Este patrón es idéntico al usado en el proyecto CV Analyzer (`cv_prompts.py`), donde el sistema y el humano tienen variables independientes.

---

## 🔗 Relaciones

- Anterior → [[Tema2-06 MessagesPlaceholder]]
- Siguiente → [[Tema2-08 Pydantic Básico]]
- Uso en proyecto → [[Tema2-11 Proyecto CV Analyzer]]
- Ver también → [[Tema2-05 ChatPromptTemplate]]
