from __future__ import annotations

import json

import aioboto3
from botocore.config import Config as BotoConfig

from .config import settings


def safe_filename(name: str | None) -> bool:
    return bool(name) and name not in (".", "..") and "/" not in name and "\\" not in name


_PUBLIC_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"AWS": ["*"]},
        "Action": ["s3:GetObject"],
        "Resource": [f"arn:aws:s3:::{settings.bucket_public}/*"],
    }],
}


class Storage:
    def __init__(self) -> None:
        self._session = aioboto3.Session()

    def _client(self, endpoint: str | None = None):
        return self._session.client(
            "s3",
            endpoint_url=endpoint or settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=BotoConfig(signature_version="s3v4"),
        )

    @property
    def buckets(self) -> list[str]:
        return [settings.bucket_uploads, settings.bucket_loot,
                settings.bucket_reports, settings.bucket_public]

    async def ensure_buckets(self) -> None:
        async with self._client() as s3:
            existing = {b["Name"] for b in (await s3.list_buckets())["Buckets"]}
            for b in self.buckets:
                if b not in existing:
                    await s3.create_bucket(Bucket=b)
            await s3.put_bucket_policy(Bucket=settings.bucket_public, Policy=json.dumps(_PUBLIC_POLICY))

    async def put(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        async with self._client() as s3:
            await s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        async with self._client() as s3:
            obj = await s3.get_object(Bucket=bucket, Key=key)
            async with obj["Body"] as stream:
                return await stream.read()

    async def stream_get(self, bucket: str, key: str, chunk_size: int = 1 << 16):
        async with self._client() as s3:
            obj = await s3.get_object(Bucket=bucket, Key=key)
            async with obj["Body"] as stream:
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

    async def presign_get(self, bucket: str, key: str, ttl: int | None = None) -> str:
        async with self._client(settings.s3_presign_endpoint) as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=ttl or settings.presign_ttl_seconds,
            )

    async def delete(self, bucket: str, key: str) -> None:
        async with self._client() as s3:
            await s3.delete_object(Bucket=bucket, Key=key)

    async def empty_bucket(self, bucket: str) -> None:
        async with self._client() as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    await s3.delete_object(Bucket=bucket, Key=obj["Key"])

    def public_url(self, key: str) -> str:
        return f"{settings.public_base_url}/{key}"


storage = Storage()
