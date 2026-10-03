from dataclasses import dataclass
from typing import Protocol


@dataclass
class SourceFile:
    id: str
    name: str
    folder_name: str


class Source(Protocol):
    def list_files(self) -> list[SourceFile]: ...

    def download(self, file: SourceFile) -> bytes: ...


def get_source() -> Source:
    from app import config

    if config.SOURCE == "drive":
        from app.adapters.drive import DriveSource

        return DriveSource(config.DRIVE_FOLDER_ID, config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_CREDENTIALS_JSON)
    from app.adapters.local import LocalSource

    return LocalSource(config.LOCAL_SOURCE_DIR)
