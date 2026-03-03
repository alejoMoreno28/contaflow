"""
drive_client.py — Wrapper para la API de Google Drive (OAuth2)

Operaciones soportadas:
  - Autenticacion OAuth2 con refresh automatico del token
  - Listar PDFs en una carpeta
  - Descargar un archivo a disco local
  - Buscar archivo por nombre en una carpeta
  - Subir o actualizar un archivo en Drive
"""

import io
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Solo pedimos acceso a Drive (lectura + escritura de archivos propios)
SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


def get_drive_service():
    """
    Autentica con Google Drive y retorna el objeto service.

    - Primera ejecucion: abre el navegador para que el usuario apruebe el acceso.
    - Ejecuciones siguientes: reutiliza el token guardado en token.json.
    """
    creds = None

    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_PATH).exists():
                raise FileNotFoundError(
                    f"No se encontro '{CREDENTIALS_PATH}'.\n"
                    "Descargalo desde Google Cloud Console > APIs y servicios > Credenciales."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def list_pdfs(service, folder_id: str) -> list[dict]:
    """
    Lista todos los PDFs (no eliminados) en la carpeta indicada.
    Retorna lista de dicts con 'id', 'name', 'createdTime'.
    """
    query = (
        f"'{folder_id}' in parents "
        f"and mimeType='application/pdf' "
        f"and trashed=false"
    )
    response = service.files().list(
        q=query,
        fields="files(id, name, createdTime)",
        orderBy="createdTime",
    ).execute()
    return response.get("files", [])


def download_file(service, file_id: str, dest_path: str):
    """Descarga el contenido de un archivo de Drive a dest_path."""
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def find_file_in_folder(service, folder_id: str, filename: str) -> str | None:
    """
    Busca un archivo por nombre exacto dentro de la carpeta.
    Retorna el ID del archivo o None si no existe.
    """
    # Las comillas simples en el nombre deben escaparse para la query de Drive
    safe_name = filename.replace("'", "\\'")
    query = (
        f"'{folder_id}' in parents "
        f"and name='{safe_name}' "
        f"and trashed=false"
    )
    response = service.files().list(q=query, fields="files(id)").execute()
    files = response.get("files", [])
    return files[0]["id"] if files else None


def upload_file(
    service,
    folder_id: str,
    local_path: str,
    mime_type: str,
    existing_id: str | None = None,
) -> str:
    """
    Sube un archivo local a Drive.
    - Si existing_id esta definido: actualiza ese archivo (mantiene su ID y URL).
    - Si no: crea uno nuevo en folder_id.
    Retorna el ID del archivo en Drive.
    """
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

    if existing_id:
        file = service.files().update(
            fileId=existing_id,
            media_body=media,
        ).execute()
    else:
        metadata = {
            "name": Path(local_path).name,
            "parents": [folder_id],
        }
        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
        ).execute()

    return file["id"]
