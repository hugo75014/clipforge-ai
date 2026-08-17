"""S3 storage provider.

A thin wrapper that uses `boto3` if installed. When boto3 isn't available
or AWS credentials are missing, `put_file` raises a helpful error so the
admin knows what's missing.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Union


class S3StorageProvider:
    name = "s3"

    def __init__(
        self,
        *,
        endpoint: str | None,
        region: str,
        bucket: str,
        access_key: str | None,
        secret_key: str | None,
        public_url: str | None = None,
    ) -> None:
        if not access_key or not secret_key:
            raise RuntimeError("S3 storage requires S3_ACCESS_KEY and S3_SECRET_KEY")
        try:
            import boto3  # noqa: F401
            from botocore.client import Config  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "S3 storage requires the 'boto3' package. Install with: pip install boto3"
            ) from exc

        import boto3
        from botocore.client import Config

        self.bucket = bucket
        self.public_url = public_url.rstrip("/") if public_url else None
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint or None,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    def put_file(self, local_path, key, content_type=None, public=True):
        extra = {"ACL": "public-read"} if public else {}
        if content_type:
            extra["ContentType"] = content_type
        self._client.upload_file(str(local_path), self.bucket, key, ExtraArgs=extra or None)
        return self.public_url(key)

    def put_bytes(self, data, key, content_type=None, public=True):
        extra = {"ACL": "public-read"} if public else {}
        if content_type:
            extra["ContentType"] = content_type
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return self.public_url(key)

    def read(self, key):
        obj = self._client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    async def stream(self, key, *, chunk_size=1 << 16):
        obj = self._client.get_object(Bucket=self.bucket, Key=key)
        body = obj["Body"]
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, body.read, chunk_size)
            if not chunk:
                break
            yield chunk

    def delete(self, key):
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key):
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def public_url(self, key):
        if self.public_url:
            return f"{self.public_url}/{key}"
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"
