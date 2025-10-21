import argparse
import os
from typing import Iterator

from dotenv import load_dotenv

from src.storage.azure_storage import AzureBlobStorage
from src.utils.logger import get_logger

logger = get_logger("upload_utils")


def iter_files(root: str) -> Iterator[str]:
    for base, _dirs, files in os.walk(root):
        for f in files:
            yield os.path.join(base, f)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Upload a local directory tree to Azure Blob using env-configured container/prefix")
    parser.add_argument("--local", required=True, help="Local directory to upload (e.g., docs)")
    parser.add_argument("--remote", required=True, help="Remote subpath under AZURE_BLOB_PREFIX (e.g., docs)")
    args = parser.parse_args()

    local_root = os.path.abspath(args.local)
    remote_root = args.remote.strip("/")

    if not os.path.isdir(local_root):
        raise SystemExit(f"Local directory not found: {local_root}")

    dbx = AzureBlobStorage()
    if not dbx.enabled():
        raise SystemExit("Azure Blob not enabled — set AZURE credentials in .env and install requirements")

    uploaded = 0
    for path in iter_files(local_root):
        rel = os.path.relpath(path, start=local_root).replace("\\", "/")
        dest_rel = f"{remote_root}/{rel}"
        ok = dbx.upload(path, dest_rel)
        if ok:
            uploaded += 1

    logger.info("uploaded %d files from %s to %s/<files>", uploaded, local_root, dbx.prefix or "/")


if __name__ == "__main__":
    main()
