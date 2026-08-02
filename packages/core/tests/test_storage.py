import pytest

from redcell_core.config import settings
from redcell_core.storage import storage


@pytest.mark.asyncio
async def test_bucket_and_roundtrip():
    await storage.ensure_buckets()
    await storage.put(settings.bucket_uploads, "t/hello.txt", b"hi", "text/plain")
    assert await storage.get_bytes(settings.bucket_uploads, "t/hello.txt") == b"hi"
    url = await storage.presign_get(settings.bucket_uploads, "t/hello.txt")
    assert "t/hello.txt" in url and "X-Amz-Signature" in url
    await storage.delete(settings.bucket_uploads, "t/hello.txt")
