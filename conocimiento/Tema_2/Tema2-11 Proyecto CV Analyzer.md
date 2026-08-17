# Tema2-11 — Proyecto CV Analyzer (App Completa)

**Carpeta:** `Tema_2/cv_analyzer/`  
**Nivel:** 🔴 Avanzado  
**Tema:** Aplicación real multi-módulo para análisis de CVs con IA  

---

## 📖 ¿Qué hace este proyecto?

Sistema completo de evaluación de currículums que:
1. Carga un PDF con el CV del candidato
2. Extrae el texto del PDF
3. Evalúa al candidato contra la descripción de un puesto usando GPT-4o-mini
4. Retorna un análisis estructurado con puntuación de ajuste al puesto
5. Muestra los resultados en una interfaz Streamlit profesional

---

## 🗂️ Estructura del Proyecto

```
cv_analyzer/
├── app.py                    → Punto de entrada
├── models/
│   └── cv_model.py           → Modelo Pydantic de salida
├── prompts/
│   └── cv_prompts.py         → Sistema de prompts del reclutador
├── services/
│   ├── cv_evaluator.py       → Cadena LCEL + lógica de evaluación
│   └── pdf_processor.py      → Extracción de texto de PDF
└── ui/
    └── streamlit_ui.py       → Interfaz de usuario completa
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `streamlit` | `streamlit` | Interfaz de usuario web |
| `ChatOpenAI` | `langchain-openai` | Modelo GPT para evaluación |
| `BaseModel, Field` | `pydantic` | Modelo de salida estructurada |
| `ChatPromptTemplate` | `langchain-core` | Sistema de prompts del reclutador |
| `SystemMessagePromptTemplate` | `langchain-core` | Prompt del sistema especializado |
| `HumanMessagePromptTemplate` | `langchain-core` | Prompt del análisis con variables |
| `PdfReader` | `pypdf` | Extracción de texto de PDF (**reemplaza PyPDF2**) |
| `BytesIO` | `io` (stdlib) | Leer PDF en memoria sin guardar en disco |

---

## 🔑 Clases y Funciones por Módulo

### `models/cv_model.py`
| Elemento | Tipo | Descripción |
|---|---|---|
| `AnalisisCV(BaseModel)` | Clase Pydantic | Define la estructura completa del análisis |
| `nombre_candidato: str` | Campo | Nombre del candidato |
| `experiencia_años: int` | Campo | Años de experiencia |
| `habilidades_clave: list[str]` | Campo | 5-7 habilidades principales |
| `education: str` | Campo | Nivel educativo |
| `experiencia_relevante: str` | Campo | Resumen de experiencia relevante |
| `fortalezas: list[str]` | Campo | 3-5 fortalezas |
| `areas_mejora: list[str]` | Campo | 2-4 áreas de mejora |
| `porcentaje_ajuste: int` | Campo | 0-100, con validación `ge=0, le=100` |

### `prompts/cv_prompts.py`
| Elemento | Tipo | Descripción |
|---|---|---|
| `SISTEMA_PROMPT` | SystemMessagePromptTemplate | Rol de reclutador experto |
| `ANALISIS_PROMPT` | HumanMessagePromptTemplate | Instrucciones de análisis con `{texto_cv}` y `{descripcion_puesto}` |
| `CHAT_PROMPT` | ChatPromptTemplate | Prompt combinado listo para usar |
| `crear_sistema_prompts()` | Función | Retorna el CHAT_PROMPT |

### `services/pdf_processor.py`
| Elemento | Tipo | Descripción |
|---|---|---|
| `PdfReader` | Clase (pypdf) | Lee el PDF en memoria |
| `extraer_texto_pdf(archivo)` | Función | Extrae texto página por página |
| `pagina.extract_text()` | Método | Extrae texto de una página del PDF |

### `services/cv_evaluator.py`
| Elemento | Tipo | Descripción |
|---|---|---|
| `crear_evaluador_cv()` | Función | Construye y retorna la cadena LCEL |
| `evaluar_candidato(texto_cv, descripcion_puesto)` | Función | Ejecuta la evaluación completa |
| `modelo_base.with_structured_output(AnalisisCV)` | Método | LLM configurado para devolver AnalisisCV |
| `cadena_evaluacion = chat_prompt \| modelo_estructurado` | LCEL | Pipeline completo |

### `ui/streamlit_ui.py`
| Elemento | Tipo | Descripción |
|---|---|---|
| `main()` | Función | Punto de entrada de la UI |
| `procesar_entrada()` | Función | Maneja upload de PDF y descripción del puesto |
| `mostrar_area_resultados()` | Función | Muestra resultados o instrucciones |
| `procesar_analisis()` | Función | Coordina extracción + evaluación + visualización |
| `mostrar_resultados(resultado)` | Función | Renderiza el análisis con métricas y colores |
| `st.file_uploader()` | Función | Componente para subir archivos |
| `st.progress()` | Función | Barra de progreso visual |
| `st.metric()` | Función | Muestra un valor principal con delta |
| `st.spinner()` | Context manager | Indicador de carga mientras procesa |

---

## 🔄 Flujo de Ejecución Completo

```
Usuario sube PDF + descripción de puesto
    ↓
extraer_texto_pdf(archivo_pdf)
  → PdfReader(BytesIO(archivo_pdf.read()))
  → pagina.extract_text() por cada página
  → texto_cv: str
    ↓
evaluar_candidato(texto_cv, descripcion_puesto)
  → crear_evaluador_cv()
  → CHAT_PROMPT | llm.with_structured_output(AnalisisCV)
  → cadena_evaluacion.invoke({"texto_cv": ..., "descripcion_puesto": ...})
  → resultado: AnalisisCV
    ↓
mostrar_resultados(resultado)
  → st.metric(porcentaje_ajuste)
  → Secciones: perfil, habilidades, fortalezas, áreas de mejora
  → Recomendación final (verde/amarillo/rojo)
```

---

## 🐛 Bug Encontrado en el Código

> [!WARNING]
> En `cv_evaluator.py` línea 192, hay un typo: `fotalezas=` en lugar de `fortalezas=`. Esto causará un error de validación Pydantic cuando se dispara la excepción. El campo correcto en `AnalisisCV` es `fortalezas`.

---

## 📝 Conceptos Aprendidos

- **Arquitectura por capas:** Separar modelos, servicios, prompts y UI
- **`pypdf` vs `PyPDF2`:** pypdf es la librería actual (PyPDF2 fue deprecado)
- **`ge=0, le=100`:** Validaciones numéricas en Pydantic (≥0, ≤100)
- **`BytesIO`:** Leer archivos en memoria sin necesidad de guardarlos en disco
- **Barra de progreso:** `st.progress()` para indicar avance en procesos largos

---

## ⚠️ Notas y Recomendaciones

> [!IMPORTANT]
> Para ejecutar: `streamlit run app.py` desde la carpeta `cv_analyzer/`

> [!TIP]
> El módulo `services/` es independiente de Streamlit. Los servicios se pueden reutilizar en APIs (FastAPI) u otras interfaces sin cambiar el código.

> [!NOTE]
> El campo `porcentaje_ajuste` usa `ge=0, le=100` para validación de rango. Esta es la forma Pydantic v2 de definir mínimos y máximos.

---

## 🔗 Relaciones

- Anterior → [[Tema2-10 Pydantic Avanzado con Keywords]]
- Siguiente → [[Tema3-01 Document Loader PDF]]
- Librerías → [[Librerías Deprecadas y Alternativas#PyPDF2 vs pypdf]]
- Patrones usados → [[Tema2-09 Structured Output con Pydantic]], [[Tema2-07 Plantilla Especializada por Rol]]
