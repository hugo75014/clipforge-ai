"""Storage service — backend-agnostic file IO.

Wraps the pluggable storage providers in `app.providers.storage` so the rest of
the app speaks a single `Storage` interface.
"""

from __future__ import annotations

import asyncio
import shutil
from functools import lru_cache
from pathlib import Path
from typing import AsyncIterator, Optional, Union

from app.core import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class Storage:
    """Thin facade over the configured storage backend.

    All methods are async. The underlying provider may be sync (local fs) or
    async (S3 / R2) — we run sync ones in a thread to keep the event loop
    responsive.
    """

    def __init__(self, backend: Optional[str] = None) -> None:
        self.backend = (backend or settings.storage_backend).lower()
        self._provider = self._build_provider(self.backend)

    # ----- factory -----
    def _build_provider(self, name: str):
        if name == "local":
            from app.providers.storage.local import LocalStorageProvider

            return LocalStorageProvider(root=settings.storage_local_root)
        if name == "s3":
            from app.providers.storage.s3 import S3StorageProvider

            return S3StorageProvider(
                endpoint=settings.s3_endpoint,
                region=settings.s3_region,
                bucket=settings.s3_bucket,
                access_key=settings.s3_access_key,
                secret_key=settings.s3_secret_key,
                public_url=settings.s3_public_url,
            )
        if name == "minio":
            from app.providers.storage.minio import MinIOStorageProvider

            return MinIOStorageProvider(
                endpoint=settings.minio_endpoint,
                port=settings.minio_port,
                bucket=settings.minio_bucket,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
        if name == "r2":
            from app.providers.storage.r2 import R2StorageProvider

            return R2StorageProvider(
                account_id=settings.r2_account_id,
                bucket=settings.r2_bucket,
                access_key=settings.r2_access_key,
                secret_key=settings.r2_secret_key,
            )
        raise ValueError(f"Unknown storage backend: {name}")

    # ----- public API -----
    @property
    def provider(self):
        return self._provider

    @property
    def is_local(self) -> bool:
        return self.backend == "local"

    async def put_file(
        self,
        local_path: Union[str, Path],
        key: str,
        *,
        content_type: Optional[str] = None,
        public: bool = True,
    ) -> str:
        """Upload a local file to the configured backend. Returns the public URL."""
        if self.is_local:
            # In local mode we copy the file into our data dir & expose via /media.
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.put_file, local_path, key, content_type, public)
        return await self._provider.put_file(local_path, key, content_type=content_type, public=public)

    async def put_bytes(
        self,
        data: bytes,
        key: str,
        *,
        content_type: Optional[str] = None,
        public: bool = True,
    ) -> str:
        if self.is_local:
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.put_bytes, data, key, content_type, public)
        return await self._provider.put_bytes(data, key, content_type=content_type, public=public)

    async def open_read(self, key: str) -> bytes:
        if self.is_local:
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.read, key)
        return await self._provider.read(key)

    async def stream(self, key: str, chunk_size: int = 1 << 16) -> AsyncIterator[bytes]:
        if self.is_local:
            data = await self.open_read(key)
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]
        else:
            async for chunk in self._provider.stream(key, chunk_size=chunk_size):
                yield chunk

    async def delete(self, key: str) -> None:
        if self.is_local:
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.delete, key)
        return await self._provider.delete(key)

    async def exists(self, key: str) -> bool:
        if self.is_local:
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.exists, key)
        return await self._provider.exists(key)

    async def public_url(self, key: str) -> str:
        if self.is_local:
            from app.providers.storage.local import LocalStorageProvider

            assert isinstance(self._provider, LocalStorageProvider)
            return await asyncio.to_thread(self._provider.public_url, key)
        return await self._provider.public_url(key)

    def local_path(self, key: str) -> Optional[Path]:
        """If the storage is local, return the absolute filesystem path of `key`."""
        if not self.is_local:
            return None
        return self._provider.abs_path(key)

    async def copy_local_into(self, local_src: Union[str, Path], key: str) -> str:
        """Copy a local file into storage and return its URL."""
        return await self.put_file(local_src, key)


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    return Storage()
