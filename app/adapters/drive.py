import io
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.adapters.base import SourceFile


class DriveSource:
    def __init__(self, folder_id: str, credentials_path: str, credentials_json: str = ""):
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        if credentials_json:
            creds = service_account.Credentials.from_service_account_info(json.loads(credentials_json), scopes=scopes)
        else:
            creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
        self.service = build("drive", "v3", credentials=creds)
        self.folder_id = folder_id

    def _children(self, folder_id: str, mime_filter: str) -> list[dict]:
        query = f"'{folder_id}' in parents and mimeType contains '{mime_filter}'"
        return self.service.files().list(q=query, fields="files(id,name)").execute().get("files", [])

    def list_files(self) -> list[SourceFile]:
        files = []
        for folder in self._children(self.folder_id, "folder"):
            for f in self._children(folder["id"], "spreadsheet"):
                files.append(SourceFile(id=f["id"], name=f["name"], folder_name=folder["name"]))
        return files

    def download(self, file: SourceFile) -> bytes:
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, self.service.files().get_media(fileId=file.id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
