# Librerías y Dependencias del Proyecto

> Referencia completa de todas las librerías usadas en `p1_lanchain`, con versiones recomendadas y estado de soporte.

---

## 📦 Dependencias por paquete pip

### Núcleo de LangChain

| Paquete pip | Versión recomendada | Módulos usados en el curso |
|---|---|---|
| `langchain` | `>=0.2` | `retrievers.multi_query` |
| `langchain-core` | `>=0.2` | `prompts`, `messages`, `runnables` |
| `langchain-community` | `>=0.2` | `vectorstores.Chroma`, `document_loaders.*` |
| `langchain-text-splitters` | `>=0.2` | `RecursiveCharacterTextSplitter` |
| `langchain-openai` | `>=0.1` | `ChatOpenAI`, `OpenAIEmbeddings` |
| `langchain-google-genai` | `>=1.0` | `ChatGoogleGenerativeAI` |
| `langchain-google-community` | `>=1.0` | `GoogleDriveLoader` |

### Modelos y APIs

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `openai` | `>=1.0` | Requerido por `langchain-openai` |
| `google-generativeai` | `>=0.7` | Requerido por `langchain-google-genai` |

### Bases de datos vectoriales

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `chromadb` | `>=0.4` | Vector store local (usado en Tema 3) |

### Procesamiento de documentos

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `pypdf` | `>=4.0` | Lectura de PDFs (**reemplaza PyPDF2**) |
| `numpy` | `>=1.24` | Operaciones matemáticas con vectores |

### Autenticación Google

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `google-auth` | `>=2.0` | Manejo de credenciales OAuth2 |
| `google-auth-oauthlib` | `>=1.0` | Flujo OAuth2 para apps de escritorio |

### Interfaz de usuario

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `streamlit` | `>=1.30` | Interfaz web interactiva |

### Validación de datos

| Paquete pip | Versión recomendada | Para qué |
|---|---|---|
| `pydantic` | `>=2.0` | Validación y serialización de datos |

---

## 🔧 Archivo requirements.txt recomendado

```txt
# LangChain
langchain>=0.2
langchain-core>=0.2
langchain-community>=0.2
langchain-text-splitters>=0.2
langchain-openai>=0.1
langchain-google-genai>=1.0
langchain-google-community>=1.0

# LLM APIs
openai>=1.0
google-generativeai>=0.7

# Vector Store
chromadb>=0.4

# Document Processing
pypdf>=4.0
numpy>=1.24

# Google Auth
google-auth>=2.0
google-auth-oauthlib>=1.0

# UI
streamlit>=1.30

# Data Validation
pydantic>=2.0
```

---

## 🔧 Instalación

```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# O instalar el entorno virtual del proyecto
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## 🔑 Variables de Entorno requeridas

| Variable | Para qué | Dónde obtenerla |
|---|---|---|
| `OPENAI_API_KEY` | Acceder a GPT y embeddings de OpenAI | [platform.openai.com](https://platform.openai.com) |
| `GOOGLE_API_KEY` | Acceder a Gemini | [Google AI Studio](https://aistudio.google.com) |

### Configuración en Windows

```powershell
# En PowerShell (sesión actual)
$env:OPENAI_API_KEY = "sk-..."
$env:GOOGLE_API_KEY = "AIza..."

# Permanente (System Properties > Environment Variables)
# O usar un archivo .env con python-dotenv
```

---

## 🔗 Relaciones

- Deprecadas → [[Librerías Deprecadas y Alternativas]]
- Buenas prácticas → [[Recomendaciones y Buenas Prácticas]]
