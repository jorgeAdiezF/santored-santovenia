import io
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.config import get_settings
from shared.exceptions import StorageError

settings = get_settings()


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_url,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket_exists(client: Minio, bucket_name: str) -> None:
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
    except S3Error as e:
        raise StorageError(f"Failed to ensure bucket exists: {str(e)}")


def upload_file(
    object_name: str,
    data: BinaryIO,
    length: int,
    content_type: str = "application/octet-stream",
    bucket_name: Optional[str] = None,
) -> str:
    client = get_minio_client()
    bucket = bucket_name or settings.minio_bucket
    ensure_bucket_exists(client, bucket)

    try:
        client.put_object(
            bucket,
            object_name,
            data,
            length=length,
            content_type=content_type,
        )
        return object_name
    except S3Error as e:
        raise StorageError(f"Failed to upload file: {str(e)}")


def upload_bytes(
    object_name: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    bucket_name: Optional[str] = None,
) -> str:
    return upload_file(
        object_name,
        io.BytesIO(data),
        len(data),
        content_type,
        bucket_name,
    )


def download_file(object_name: str, bucket_name: Optional[str] = None) -> bytes:
    client = get_minio_client()
    bucket = bucket_name or settings.minio_bucket

    try:
        response = client.get_object(bucket, object_name)
        return response.read()
    except S3Error as e:
        raise StorageError(f"Failed to download file: {str(e)}")
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(
    object_name: str,
    expires_seconds: int = 3600,
    bucket_name: Optional[str] = None,
) -> str:
    client = get_minio_client()
    bucket = bucket_name or settings.minio_bucket

    try:
        from datetime import timedelta
        url = client.presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(seconds=expires_seconds),
        )
        return url
    except S3Error as e:
        raise StorageError(f"Failed to generate presigned URL: {str(e)}")


def delete_object(object_name: str, bucket_name: Optional[str] = None) -> None:
    client = get_minio_client()
    bucket = bucket_name or settings.minio_bucket

    try:
        client.remove_object(bucket, object_name)
    except S3Error as e:
        raise StorageError(f"Failed to delete object: {str(e)}")


def object_exists(object_name: str, bucket_name: Optional[str] = None) -> bool:
    client = get_minio_client()
    bucket = bucket_name or settings.minio_bucket

    try:
        client.stat_object(bucket, object_name)
        return True
    except S3Error:
        return False
