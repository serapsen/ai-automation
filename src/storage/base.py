from typing import Protocol
import os

class IStorage(Protocol):
    def enabled(self) -> bool: ...
    def upload(self, local_path: str, dest_rel_path: str) -> bool: ...


def get_storage():
    backend = (os.getenv("STORAGE_BACKEND") or "azure").lower()
    if backend == "none":
        return _NullStorage()
    try:
        from src.storage.azure_storage import AzureBlobStorage  # type: ignore
        return AzureBlobStorage()
    except Exception:
        return _NullStorage()


class _NullStorage:
    def enabled(self) -> bool:
        return False

    def upload(self, local_path: str, dest_rel_path: str) -> bool:
        return False
