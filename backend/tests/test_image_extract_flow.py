import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from routers import image as image_router
from services.algo_client import AlgoServiceError


class FakeUploadFile:
    def __init__(self, filename="sample.png", content_type="image/png", content=b"fake-image-bytes"):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


class TestExtractWatermarkRouter(unittest.IsolatedAsyncioTestCase):
    async def test_extract_watermark_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_file = FakeUploadFile()

            with patch("routers.image.BIZ_IMAGE_STORAGE_ROOT", temp_dir), patch(
                "routers.image.crud_auth.verify_session_token",
                new=AsyncMock(return_value={"id": 1, "username": "alice"}),
            ), patch(
                "routers.image.algo_client.extract_watermark_from_image",
                new=AsyncMock(
                    return_value={
                        "extracted_watermark": "01010101010101010101010101010101",
                        "elapsed_ms": 321,
                    }
                ),
            ):
                response = await image_router.extract_watermark(
                    image_file=fake_file,
                    authorization="Bearer token-123",
                )

            self.assertEqual(response["watermark_bits"], "01010101010101010101010101010101")
            self.assertEqual(response["elapsed_ms"], 321)
            self.assertEqual(response["file_name"], "sample.png")
            self.assertEqual(response["file_size_bytes"], len(b"fake-image-bytes"))
            saved_files = list(Path(temp_dir).rglob("source.png"))
            self.assertTrue(saved_files)

    async def test_extract_watermark_returns_401_without_token(self):
        fake_file = FakeUploadFile()

        with self.assertRaises(HTTPException) as ctx:
            await image_router.extract_watermark(
                image_file=fake_file,
                authorization=None,
            )

        self.assertEqual(ctx.exception.status_code, 401)

    async def test_extract_watermark_maps_algo_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_file = FakeUploadFile()

            with patch("routers.image.BIZ_IMAGE_STORAGE_ROOT", temp_dir), patch(
                "routers.image.crud_auth.verify_session_token",
                new=AsyncMock(return_value={"id": 1, "username": "alice"}),
            ), patch(
                "routers.image.algo_client.extract_watermark_from_image",
                new=AsyncMock(side_effect=AlgoServiceError("算法服务不可达", status_code=503)),
            ):
                with self.assertRaises(HTTPException) as ctx:
                    await image_router.extract_watermark(
                        image_file=fake_file,
                        authorization="Bearer token-123",
                    )

        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
