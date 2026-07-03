import os
from pathlib import Path
import urllib.parse
from backend import config as app_config

class FileStorageService:
    @staticmethod
    def is_s3_enabled() -> bool:
        """
        Check if S3 settings are configured and available.
        """
        return bool(app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY and app_config.AWS_STORAGE_BUCKET_NAME)

    @staticmethod
    def upload_file(local_path: Path) -> str:
        """
        Uploads a local file to S3 if configured.
        Returns 's3://bucket/key' if uploaded, otherwise returns the absolute local path.
        """
        if not local_path.is_file():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        filename = local_path.name
        
        if FileStorageService.is_s3_enabled():
            s3_client = app_config.get_s3_client()
            if s3_client:
                key = f"uploads/{filename}"
                bucket = app_config.AWS_STORAGE_BUCKET_NAME
                try:
                    print(f"[storage] Uploading {filename} to S3 bucket {bucket}...")
                    s3_client.upload_file(str(local_path), bucket, key)
                    s3_url = f"s3://{bucket}/{key}"
                    print(f"[storage] Uploaded successfully: {s3_url}")
                    return s3_url
                except Exception as e:
                    print(f"[storage] S3 upload failed, falling back to local: {e}")
                    return str(local_path)
        
        # Fallback to local path string
        return str(local_path)

    @staticmethod
    def ensure_local_file(file_path_or_url: str) -> Path:
        """
        Ensures the requested file is present on the local filesystem.
        If it is an S3 URI (s3://bucket/key) and the file is missing locally,
        downloads it from S3.
        Returns the Path to the local file.
        """
        if file_path_or_url.startswith("s3://"):
            # Parse s3 URI
            parsed = urllib.parse.urlparse(file_path_or_url)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            filename = Path(key).name
            
            # Local cache path
            local_dest = app_config.PROJECT_ROOT / "data" / "uploads" / filename
            local_dest.parent.mkdir(parents=True, exist_ok=True)
            
            if local_dest.is_file():
                # Already exists locally, return it
                return local_dest
            
            # Need to download from S3
            if FileStorageService.is_s3_enabled():
                s3_client = app_config.get_s3_client()
                if s3_client:
                    try:
                        print(f"[storage] Local cache miss. Downloading {key} from S3 bucket {bucket}...")
                        s3_client.download_file(bucket, key, str(local_dest))
                        print(f"[storage] Download complete: {local_dest}")
                        return local_dest
                    except Exception as e:
                        raise FileNotFoundError(f"Failed to download file from S3: {e}")
                else:
                    raise ValueError("S3 client could not be initialized, cannot download s3 URI.")
            else:
                raise ValueError("S3 storage is not configured, cannot download s3 URI.")
        
        # It's a standard local path
        local_path = Path(file_path_or_url)
        if not local_path.is_file():
            # If the local file is missing, try to see if S3 has it under uploads/{filename}
            # This handles cases where database references S3 but a local path was stored,
            # or the container restarted and has an old local path structure.
            filename = local_path.name
            bucket = app_config.AWS_STORAGE_BUCKET_NAME
            key = f"uploads/{filename}"
            local_dest = app_config.PROJECT_ROOT / "data" / "uploads" / filename
            
            if FileStorageService.is_s3_enabled():
                s3_client = app_config.get_s3_client()
                if s3_client:
                    try:
                        print(f"[storage] Local file {filename} missing. Attempting fallback download from S3...")
                        s3_client.download_file(bucket, key, str(local_dest))
                        return local_dest
                    except Exception:
                        pass # Fail silently and let standard error raise below
            
            raise FileNotFoundError(f"Local file not found and could not be recovered: {local_path}")
            
        return local_path
