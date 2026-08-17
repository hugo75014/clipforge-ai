"""MinIO storage provider."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Union


class MinIOStorageProvider:
    name = "minio"

    def __init__(
        self,
        *,
        endpoint: str | None,
        port: int,
        bucket: str,
        access_key: str | None,
        secret_key: str | None,
        secure: bool = False,
    ) -> None:
        if not endpoint or not access_key or not secret_key:
            raise RuntimeError("MinIO storage requires MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY")
        try:
            from minio import Minio  # noqa: F401
            from minio.error import S3Error  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "MinIO storage requires the 'minio' package. Install with: pip install minio"
            ) from exc

        from minio import Minio

        self.bucket = bucket
        self._client = Minio(
            f"{endpoint}:{port}",
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        # Ensure bucket exists.
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def put_file(self, local_path, key, content_type=None, public=True):
        self._client.fput_object(self.bucket, key, str(local_path), content_type=content_type)
        return self.public_url(key)

    def put_bytes(self, data, key, content_type=None, public=True):
        import io

        self._client.put_object(
            self.bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
        )
        return self.public_url(key)

    def read(self, key):
        resp = self._client.get_object(self.bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
        return b""

    async def stream(self, key, *, chunk_size=1 << 16):
        resp = self._client.get_object(self.bucket, key)
        try:
            while True:
                chunk = resp.stream(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            resp.close()

    def delete(self, key):
        self._client.remove_object(self.bucket, key)

    def exists(self, key):
        try:
            self._client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False

    def public_url(self, key):
        return f"{self._client._base_url.bucket}/{self.bucket}/{key}"
