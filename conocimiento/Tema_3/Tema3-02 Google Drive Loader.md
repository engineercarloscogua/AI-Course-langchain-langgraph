# Tema3-02 — Google Drive Loader con OAuth2

**Archivo:** `Tema_3/2-google_drive.py`  
**Nivel:** 🔴 Avanzado  
**Tema:** Autenticación OAuth2 y carga de documentos desde Google Drive  

---

## 📖 ¿Qué hace este archivo?

Conecta LangChain con Google Drive usando autenticación OAuth2. Carga documentos desde una carpeta de Drive específica y los convierte en objetos `Document` de LangChain.

---

## 💻 Código clave

```python
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from langchain_google_community import GoogleDriveLoader

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Cargar token existente si ya se autenticó
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

# Si no hay token válido, autenticar
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Renovar automáticamente
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)  # Abre navegador para login

    with open("token.json", "w") as f:
        f.write(creds.to_json())

# Cargar documentos
loader = GoogleDriveLoader(folder_id="1I7ram2I2XXYnJMOLFsrPjipNTX4faqHT", credentials=creds)
documents = loader.load()
```

---

## 📦 Librerías Usadas

| Librería | Paquete pip | Para qué |
|---|---|---|
| `Credentials` | `google-auth` | Manejo de credenciales OAuth2 |
| `InstalledAppFlow` | `google-auth-oauthlib` | Flujo OAuth para apps de escritorio |
| `Request` | `google-auth` | Renovar tokens expirados |
| `GoogleDriveLoader` | `langchain-google-community` | Cargar documentos de Drive |

---

## 🔑 Clases y Funciones

| Elemento | Tipo | Descripción |
|---|---|---|
| `Credentials` | Clase | Objeto que contiene el token de acceso OAuth2 |
| `InstalledAppFlow` | Clase | Gestiona el flujo de autenticación OAuth2 |
| `.from_client_secrets_file(path, scopes)` | Método | Lee credenciales del archivo descargado de Google Cloud |
| `.run_local_server(port=0)` | Método | Abre el navegador para que el usuario inicie sesión |
| `creds.refresh(Request())` | Método | Renueva el token de acceso usando el refresh_token |
| `creds.to_json()` | Método | Serializa las credenciales para guardarlas en disco |
| `GoogleDriveLoader(folder_id, credentials)` | Clase | Loader de LangChain para Google Drive |
| `.load()` | Método | Descarga y convierte documentos a objetos `Document` |

---

## 🔑 Flujo OAuth2 — Patrón estándar

```
1. Verificar si existe token.json → credenciales guardadas
      ↓ Si existe
2. Cargar credenciales: Credentials.from_authorized_user_file()
      ↓
3. ¿Son válidas? 
   - Sí → usar directamente
   - Expiradas con refresh_token → creds.refresh(Request()) → renovar silenciosamente
   - No hay token → InstalledAppFlow → abre navegador → usuario hace login → guardar token
      ↓
4. GoogleDriveLoader(folder_id, credentials).load()
```

---

## 🔐 Concepto Clave: OAuth2

> **OAuth2** es el estándar de autorización que permite a una aplicación acceder a recursos de Google (Drive, Gmail, etc.) con los permisos del usuario, sin que la app tenga que conocer la contraseña.

| Archivo | Descripción |
|---|---|
| `credentials_langchain.json` | Secreto del cliente descargado de Google Cloud Console |
| `token.json` | Token de acceso generado tras el primer login (se renueva automáticamente) |

---

## 🔐 Configuración Necesaria

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar **Google Drive API**
3. Crear credenciales OAuth 2.0 (aplicación de escritorio)
4. Descargar `credentials.json`
5. Primera ejecución: abre el navegador para autorización

---

## 📝 Conceptos Aprendidos

- **OAuth2:** Protocolo de autorización estándar para APIs de Google
- **Scopes:** Permisos específicos solicitados (`drive.readonly`)
- **Token de acceso:** Credencial temporal para acceder a la API
- **Refresh token:** Token de larga vida que permite renovar el access token
- **`folder_id`:** ID de la carpeta de Drive (del URL de Google Drive)

---

## ⚠️ Notas y Recomendaciones

> [!IMPORTANT]
> Nunca commitees `credentials_langchain.json` ni `token.json` al repositorio. Agrégalos al `.gitignore`.

> [!TIP]
> El `folder_id` es la parte del URL de Google Drive después de `/folders/`: `https://drive.google.com/drive/folders/**TU_FOLDER_ID**`

> [!NOTE]
> `langchain_google_community` es el paquete correcto (2024+). El antiguo `langchain_community.document_loaders.googledrive` está deprecado.

---

## 🔗 Relaciones

- Anterior → [[Tema3-01 Document Loader PDF]]
- Siguiente → [[Tema3-03 Text Splitter Parte 1]]
- Comparación de loaders → [[Tema3-01 Document Loader PDF#Ecosistema de Document Loaders]]
- Deprecaciones → [[Librerías Deprecadas y Alternativas#Google Drive Loader]]
