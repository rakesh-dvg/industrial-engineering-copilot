"""MinIO object storage for product documents."""

from __future__ import annotations

import io

from minio import Minio
from minio.error import S3Error

from app.config import Settings, get_settings


class ObjectStorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = Minio(
            self._settings.minio_endpoint,
            access_key=self._settings.minio_access_key,
            secret_key=self._settings.minio_secret_key,
            secure=self._settings.minio_secure,
        )
        self._bucket = self._settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> str:
        self.ensure_bucket()
        self._client.put_object(
            self._bucket,
            object_key,
            io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )
        return object_key

    def download_bytes(self, object_key: str) -> bytes:
        try:
            response = self._client.get_object(self._bucket, object_key)
        except S3Error as exc:
            raise FileNotFoundError(object_key) from exc
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


def get_object_storage(settings: Settings | None = None) -> ObjectStorageService:
    return ObjectStorageService(settings)
