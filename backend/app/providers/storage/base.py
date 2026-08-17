"""Storage provider protocol — anything we swap in must implement this."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator, Protocol, Union


class StorageProvider(Protocol):
    name: str

    def put_file(
        self,
        local_path: Union[str, Path],
        key: str,
        content_type: str | None = None,
        public: bool = True,
    ) -> str: ...

    def put_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str | None = None,
        public: bool = True,
    ) -> str: ...

    def read(self, key: str) -> bytes: ...

    def stream(self, key: str, *, chunk_size: int = 1 << 16) -> AsyncIterator[bytes]: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...

    def public_url(self, key: str) -> str: ...
