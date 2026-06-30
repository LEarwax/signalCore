"""
storage_service.py — S3 in prod, local /tmp in dev.

If AWS_ACCESS_KEY_ID is set, uses S3.
Otherwise writes to LOCAL_DIR and returns /api/files/<key> URLs.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

LOCAL_DIR = Path("/tmp/signalcore")
_USE_S3 = bool(os.getenv("AWS_ACCESS_KEY_ID"))


class StorageService:

    def __init__(self) -> None:
        if _USE_S3:
            import boto3
            self._s3 = boto3.client("s3")
            self._bucket = os.getenv("S3_BUCKET", "signalcore-dev")
        else:
            LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store data and return a URL (S3 presigned or local API path)."""
        if _USE_S3:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return f"https://{self._bucket}.s3.amazonaws.com/{key}"
        else:
            path = LOCAL_DIR / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return f"/api/files/{key}"

    def download(self, key: str) -> bytes:
        """Retrieve data by storage key."""
        if _USE_S3:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()
        else:
            return (LOCAL_DIR / key).read_bytes()

    def key_exists(self, key: str) -> bool:
        if _USE_S3:
            try:
                self._s3.head_object(Bucket=self._bucket, Key=key)
                return True
            except Exception:
                return False
        return (LOCAL_DIR / key).exists()


# Module-level singleton
storage = StorageService()
