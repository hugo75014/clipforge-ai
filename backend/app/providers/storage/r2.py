"""Cloudflare R2 storage provider.

R2 is S3-compatible; we re-use boto3 with a custom endpoint.
"""

from __future__ import annotations

from app.providers.storage.s3 import S3StorageProvider


class R2StorageProvider(S3StorageProvider):
    name = "r2"

    def __init__(
        self,
        *,
        account_id: str | None,
        bucket: str,
        access_key: str | None,
        secret_key: str | None,
    ) -> None:
        if not account_id:
            raise RuntimeError("R2 storage requires R2_ACCOUNT_ID")
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        public_url = f"https://{bucket}.{account_id}.r2.dev"
        super().__init__(
            endpoint=endpoint,
            region="auto",
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
            public_url=public_url,
        )
