"""Local-filesystem storage provider.

Files live under `root`. Each `key` is mapped to `<root>/<key>` after a
sanitization pass. The `public_url` is built using
`settings.storage_public_base_url`, which the API serves via the /media
mount (see `app.api.v1.media`).
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Iterator, Union

from shared.utils import safe_filename

_SAFE_KEY = re.compile(r"^[A-Za-z0-9._/\-]+$")


def _sanitize_key(key: str) -> str:
    """Allow slashes but strip anything dangerous."""
    parts: list[str] = []
    for p in key.replace("\\", "/").split("/"):
        if not p or p == ".":
            continue
        if p == "..":
            # Drop any ".."
            continue
        parts.append(safe_filename(p, fallback="file"))
    return "/".join(parts) or "file"


class LocalStorageProvider:
    name = "local"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ----- internal helpers -----
    def _resolve(self, key: str) -> Path:
        if not _SAFE_KEY.match(key):
            key = _sanitize_key(key)
        path = (self.root / key).resolve()
        # Defensive: never let a key escape the root.
        if not str(path).startswith(str(self.root)):
            raise ValueError(f"path escapes storage root: {key!r}")
        return path

    def abs_path(self, key: str) -> Path:
        return self._resolve(key)

    # ----- public API -----
    def put_file(
        self,
        local_path: Union[str, Path],
        key: str,
        content_type: str | None = None,
        public: bool = True,
    ) -> str:
        src = Path(local_path)
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"local file not found: {src}")
        dst = self._resolve(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # cross-fs safe copy
        shutil.copyfile(src, dst)
        return self.public_url(key)

    def put_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str | None = None,
        public: bool = True,
    ) -> str:
        dst = self._resolve(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
        return self.public_url(key)

    def read(self, key: str) -> bytes:
        p = self._resolve(key)
        if not p.exists():
            raise FileNotFoundError(f"key not found: {key}")
        return p.read_bytes()

    def stream(self, key: str, *, chunk_size: int = 1 << 16) -> Iterator[bytes]:
        p = self._resolve(key)
        if not p.exists():
            raise FileNotFoundError(f"key not found: {key}")
        with open(p, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def delete(self, key: str) -> None:
        p = self._resolve(key)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists():
            p.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def public_url(self, key: str) -> str:
        from app.core import settings

        base = settings.storage_public_base_url.rstrip("/")
        # url-encode the path parts (but keep slashes)
        return f"{base}/{key}"
