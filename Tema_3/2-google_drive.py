# leer documentos de google drive
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from langchain_google_community import GoogleDriveLoader

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

BASE_DIR = Path(__file__).resolve().parent
credentials_path = BASE_DIR / "credentials_langchain.json"
token_path = BASE_DIR / "token.json"
folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

if not folder_id:
    raise RuntimeError("Configura GOOGLE_DRIVE_FOLDER_ID como variable de entorno.")

# --- Autenticación OAuth manual ---
creds = None

# Cargar token existente si ya se autenticó antes
if token_path.exists():
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

# Si no hay credenciales válidas, iniciar flujo de autenticación
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Renovar token automáticamente
    else:
        # Abrirá el navegador para que inicies sesión con Google
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    # Guardar el token para la próxima ejecución
    with token_path.open("w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())

# --- Cargar documentos de Google Drive ---
loader = GoogleDriveLoader(
    folder_id=folder_id,
    credentials=creds,
)

documents = loader.load()

# Ver documentos individuales
print(f"\nTotal de documentos cargados: {len(documents)}")
print(f"\nMetadatos : {documents[0].metadata}")
print(f"Contenido : {documents[0].page_content}")
