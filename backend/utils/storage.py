import os
import shutil
from pathlib import Path


class FileStorageService:
    """
    Unified file storage service supporting Azure Blob Storage with local fallback.

    If AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER_NAME are set,
    files are uploaded to Azure Blob Storage on write and downloaded on demand (cache miss).

    If Azure credentials are absent, the service is a transparent pass-through
    to the local filesystem — zero configuration needed for local development.
    """

    # Cache directory for locally restored blobs
    _CACHE_DIR: Path = Path("/app/data/uploads") if os.path.exists("/app") else (
        Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
    )

    @staticmethod
    def is_azure_enabled() -> bool:
        """Returns True only if all required Azure credentials are configured."""
        from backend.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME
        return bool(AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER_NAME)

    @staticmethod
    def _get_client():
        """Returns a configured BlobServiceClient, or None."""
        if not FileStorageService.is_azure_enabled():
            return None
        try:
            from azure.storage.blob import BlobServiceClient
            from backend.config import AZURE_STORAGE_CONNECTION_STRING
            return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        except Exception as e:
            print(f"[storage] Failed to init Azure client: {e}")
            return None

    @staticmethod
    def upload_file(local_path: Path | str) -> str:
        """
        Upload a file to Azure Blob Storage and return an 'azure://<container>/<blob>' URI.
        Falls back to returning the local path string if Azure is not configured.

        Args:
            local_path: Path to the local file to upload.

        Returns:
            'azure://<container>/<blob_name>' if Azure is enabled, else str(local_path).
        """
        local_path = Path(local_path)

        if not FileStorageService.is_azure_enabled():
            return str(local_path)

        client = FileStorageService._get_client()
        if client is None:
            return str(local_path)

        try:
            from backend.config import AZURE_STORAGE_CONTAINER_NAME
            blob_name = local_path.name
            container_client = client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)

            # Create container if it doesn't exist
            try:
                container_client.create_container()
            except Exception:
                pass  # Already exists

            with open(local_path, "rb") as f:
                container_client.upload_blob(name=blob_name, data=f, overwrite=True)

            print(f"[storage] Uploaded '{blob_name}' to Azure Blob Storage.")
            return f"azure://{AZURE_STORAGE_CONTAINER_NAME}/{blob_name}"

        except Exception as e:
            print(f"[storage] Azure upload failed for '{local_path.name}': {e} — using local path.")
            return str(local_path)

    @staticmethod
    def ensure_local_file(file_path: str) -> Path:
        """
        Resolve a file path to a local Path, downloading from Azure if needed.

        Accepts:
          - 'azure://<container>/<blob_name>'  → downloads blob if not cached locally
          - Local path string                  → resolves and returns directly

        Returns:
            A Path object pointing to the local file (guaranteed to exist).

        Raises:
            FileNotFoundError if the file cannot be found or downloaded.
        """
        if file_path.startswith("azure://"):
            # Parse azure://<container>/<blob_name>
            rest = file_path[len("azure://"):]
            parts = rest.split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"[storage] Invalid Azure URI: {file_path}")
            container_name, blob_name = parts

            # Check local cache first
            FileStorageService._CACHE_DIR.mkdir(parents=True, exist_ok=True)
            local_cache = FileStorageService._CACHE_DIR / blob_name

            if local_cache.exists():
                return local_cache

            # Download from Azure
            client = FileStorageService._get_client()
            if client is None:
                raise FileNotFoundError(f"[storage] Azure client unavailable, cannot download: {file_path}")

            try:
                print(f"[storage] Cache miss — downloading '{blob_name}' from Azure...")
                blob_client = client.get_blob_client(container=container_name, blob=blob_name)
                with open(local_cache, "wb") as f:
                    data = blob_client.download_blob()
                    data.readinto(f)
                print(f"[storage] Downloaded '{blob_name}' to local cache.")
                return local_cache

            except Exception as e:
                raise FileNotFoundError(
                    f"[storage] Failed to download '{blob_name}' from Azure: {e}"
                )

        else:
            # Local path — resolve it
            from backend.config import PROJECT_ROOT
            path = Path(file_path)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            path = path.resolve()

            if not path.exists():
                raise FileNotFoundError(f"[storage] File not found: {path}")

            return path
