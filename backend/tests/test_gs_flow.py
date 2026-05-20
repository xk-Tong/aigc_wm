import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from routers import gs as gs_router
from schemas.gs import GenerateWatermarkedGSRequest
from services.algo_client import AlgoServiceError


class _FakeRequest:
    @staticmethod
    def url_for(name: str, **params):
        if name != "storage_gs":
            raise ValueError("unexpected route name")
        return f"http://localhost:8000/storage_gs/{params['path']}"


class TestGSGenerateRouter(unittest.IsolatedAsyncioTestCase):
    async def test_generate_watermarked_gs_success(self):
        body = GenerateWatermarkedGSRequest(
            prompt="a cute cat",
            model="gaussian-splatting",
            watermark_bits="01010101010101010101010101010101",
        )

        fake_gs_bytes = b"ply\nformat binary_little_endian 1.0\nend_header\n" + b"\x00" * 68

        with patch(
            "routers.gs.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ), patch(
            "routers.gs.algo_client.generate_watermarked_gs",
            new=AsyncMock(
                return_value=(fake_gs_bytes, "ply", 500, 100)
            ),
        ):
            response = await gs_router.generate_watermarked_gs(
                body=body,
                request=_FakeRequest(),
                authorization="Bearer token-123",
            )

        self.assertIn("gs_id", response)
        self.assertIn("gs_url", response)
        self.assertIn("download_url", response)
        self.assertEqual(response["watermark_bits"], body.watermark_bits)
        self.assertEqual(response["gaussian_count"], 100)
        self.assertEqual(response["file_format"], "ply")

    async def test_generate_watermarked_gs_returns_401_without_token(self):
        body = GenerateWatermarkedGSRequest(
            prompt="a cute cat",
            model="gaussian-splatting",
            watermark_bits="01010101010101010101010101010101",
        )

        with self.assertRaises(HTTPException) as ctx:
            await gs_router.generate_watermarked_gs(
                body=body,
                request=_FakeRequest(),
                authorization=None,
            )

        self.assertEqual(ctx.exception.status_code, 401)

    async def test_generate_watermarked_gs_maps_algo_error(self):
        body = GenerateWatermarkedGSRequest(
            prompt="a cute cat",
            model="gaussian-splatting",
            watermark_bits="01010101010101010101010101010101",
        )

        with patch(
            "routers.gs.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ), patch(
            "routers.gs.algo_client.generate_watermarked_gs",
            new=AsyncMock(side_effect=AlgoServiceError("3DGS算法服务不可达", status_code=503)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await gs_router.generate_watermarked_gs(
                    body=body,
                    request=_FakeRequest(),
                    authorization="Bearer token-123",
                )

        self.assertEqual(ctx.exception.status_code, 503)


class TestGSExtractRouter(unittest.IsolatedAsyncioTestCase):
    async def test_extract_watermark_success(self):
        """正常提取流程。"""

        class _FakeUploadFile:
            filename = "test.ply"
            content_type = "application/octet-stream"

            async def read(self):
                return b"ply\nformat binary_little_endian 1.0\nend_header\n" + b"\x00" * 68

        with patch(
            "routers.gs.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ), patch(
            "routers.gs.algo_client.extract_watermark_from_gs",
            new=AsyncMock(
                return_value={
                    "extracted_watermark": "10101010101010101010101010101010",
                    "elapsed_ms": 200,
                }
            ),
        ):
            response = await gs_router.extract_watermark(
                gs_file=_FakeUploadFile(),
                authorization="Bearer token-123",
            )

        self.assertIn("file_id", response)
        self.assertEqual(response["watermark_bits"], "10101010101010101010101010101010")
        self.assertEqual(response["file_name"], "test.ply")

    async def test_extract_rejects_empty_file(self):
        """空文件拒绝。"""

        class _FakeUploadFile:
            filename = "test.ply"
            content_type = "application/octet-stream"

            async def read(self):
                return b""

        with patch(
            "routers.gs.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await gs_router.extract_watermark(
                    gs_file=_FakeUploadFile(),
                    authorization="Bearer token-123",
                )

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_extract_rejects_invalid_extension(self):
        """非 PLY 文件拒绝。"""

        class _FakeUploadFile:
            filename = "test.obj"
            content_type = "application/octet-stream"

            async def read(self):
                return b"fake content"

        with patch(
            "routers.gs.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await gs_router.extract_watermark(
                    gs_file=_FakeUploadFile(),
                    authorization="Bearer token-123",
                )

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
