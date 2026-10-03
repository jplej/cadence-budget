from pathlib import Path

from app.adapters.base import SourceFile


class LocalSource:
    # Mirrors the Drive layout: <root>/<ARTIST_FOLDER>/<file>.xlsx, no recursion.
    def __init__(self, root: str):
        self.root = Path(root)

    def list_files(self) -> list[SourceFile]:
        if not self.root.is_dir():
            raise FileNotFoundError(f"Local source folder not found: {self.root}")
        return [
            SourceFile(id=str(p.relative_to(self.root)), name=p.name, folder_name=p.parent.name)
            for folder in sorted(self.root.iterdir()) if folder.is_dir()
            for p in sorted(folder.glob("*.xlsx"))
        ]

    def download(self, file: SourceFile) -> bytes:
        return (self.root / file.id).read_bytes()
