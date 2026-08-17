# Storage backends

The `Storage` facade in `backend/app/services/storage/` is the only thing
the rest of the app talks to. It delegates to a `StorageProvider` based on
`STORAGE_BACKEND` in `.env`.

```text
StorageProvider
 ├── LocalStorageProvider      (default — files on disk)
 ├── S3StorageProvider         (boto3 — any S3-compatible)
 ├── MinIOStorageProvider      (MinIO — S3-compatible)
 └── R2StorageProvider         (Cloudflare R2 — S3-compatible)
```

The facade exposes:

```python
await storage.put_file(local_path, key, content_type=...)  # → public_url
await storage.put_bytes(data, key, content_type=...)        # → public_url
await storage.open_read(key)                                # → bytes
async for chunk in storage.stream(key): ...                 # → AsyncIterator[bytes]
await storage.delete(key)
await storage.exists(key)                                   # → bool
storage.public_url(key)                                     # → str
```

## Local mode (default)

```env
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=/app/data
STORAGE_PUBLIC_BASE_URL=http://localhost:8000/media
```

Files are written under `STORAGE_LOCAL_ROOT`. The backend exposes them
through the `/media` mount (or through `/uploads` and `/outputs` in dev).

## S3

```env
STORAGE_BACKEND=s3
S3_ENDPOINT=https://s3.amazonaws.com
S3_REGION=us-east-1
S3_BUCKET=clipforge
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_PUBLIC_URL=https://clipforge.s3.amazonaws.com   # optional CDN URL
```

Install the optional dependency: `pip install boto3`.

## MinIO

```env
STORAGE_BACKEND=minio
MINIO_ENDPOINT=minio.example.com
MINIO_PORT=9000
MINIO_BUCKET=clipforge
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_SECURE=false
```

Install: `pip install minio`.

## Cloudflare R2

```env
STORAGE_BACKEND=r2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
R2_BUCKET=clipforge
```

R2 is S3-compatible under the hood — we reuse `boto3`.

## Adding a new backend

1. Create `backend/app/providers/storage/mybackend.py` implementing the
   `StorageProvider` protocol.
2. Register it in `backend/app/services/storage/__init__.py`.
3. Document it here.

## Public URLs vs. signed URLs

By default we set `ACL=public-read` on uploaded objects so the front-end
can stream them directly. For private buckets, switch to signed URLs by
overriding `public_url()` to return a short-lived presigned URL.
