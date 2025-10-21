import os
from typing import Optional

from dotenv import load_dotenv

try:
    from azure.storage.blob import BlobServiceClient
except Exception:  # pragma: no cover
    BlobServiceClient = None  # type: ignore

from src.utils.logger import get_logger

logger = get_logger("azure_storage")


class AzureBlobStorage:
    """Minimal Azure Blob uploader enabled via environment variables.

    Env vars:
      - AZURE_STORAGE_CONNECTION_STRING: preferred way to auth
        OR
      - AZURE_STORAGE_ACCOUNT + AZURE_STORAGE_KEY: alternate auth
      - AZURE_BLOB_CONTAINER: required container name
      - AZURE_BLOB_PREFIX: optional path prefix inside the container (e.g., "ai-automation-images")
    """

    def __init__(self) -> None:
        load_dotenv()
        self.conn_str: Optional[str] = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.account: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.key: Optional[str] = os.getenv("AZURE_STORAGE_KEY")
        self.container: Optional[str] = os.getenv("AZURE_BLOB_CONTAINER")
        self.prefix: str = (os.getenv("AZURE_BLOB_PREFIX") or "").strip().strip("/")
        self._client: Optional[BlobServiceClient] = None

        if BlobServiceClient is None:
            logger.warning("azure.storage.blob SDK not installed; skipping cloud upload")
            return
        if not self.container:
            logger.info("Azure Blob disabled (AZURE_BLOB_CONTAINER not set)")
            return
        try:
            if self.conn_str:
                self._client = BlobServiceClient.from_connection_string(self.conn_str)
            elif self.account and self.key:
                self._client = BlobServiceClient(
                    account_url=f"https://{self.account}.blob.core.windows.net",
                    credential=self.key,
                )
            else:
                logger.info("Azure Blob disabled (no credentials in env)")
                return
            # simple check: list containers to validate auth
            _ = [c.name for c in self._client.list_containers(name_starts_with=self.container)][:1]
            logger.info("Azure Blob enabled: container=%s prefix=%s", self.container, self.prefix or "/")
        except Exception as e:  # pragma: no cover
            logger.error("Azure Blob init failed: %s", e)
            self._client = None

    def enabled(self) -> bool:
        return bool(self._client and self.container)

    def _blob_path(self, rel_path: str) -> str:
        rel = rel_path.replace("\\", "/").lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{rel}"
        return rel

    def upload(self, local_path: str, dest_rel_path: str) -> bool:
        """Upload a single file to Azure Blob at container/prefix/dest_rel_path.
        Returns True on success.
        """
        if not self.enabled():
            return False
        try:
            blob_name = self._blob_path(dest_rel_path)
            container_client = self._client.get_container_client(self.container)  # type: ignore[arg-type]
            # Create container if it doesn't exist
            try:
                container_client.create_container()
            except Exception:
                pass
            with open(local_path, "rb") as data:
                container_client.upload_blob(name=blob_name, data=data, overwrite=True)
            logger.info("uploaded to azure blob -> %s/%s", self.container, blob_name)
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Azure Blob upload failed for %s: %s", local_path, e)
            return False
