import base64
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from routers import image as image_router
from schemas.image import GenerateWatermarkedImageRequest
from services.algo_client import AlgoServiceError


class _FakeRequest:
    @staticmethod
    def url_for(name: str, **params):
        if name != "storage":
            raise ValueError("unexpected route name")
        return f"http://localhost:8000/storage/{params['path']}"


class TestImageRouter(unittest.IsolatedAsyncioTestCase):
    async def test_generate_watermarked_image_success(self):
        body = GenerateWatermarkedImageRequest(
            prompt="a cat",
            model="flux2",
            watermark_bits="01010101010101010101010101010101",
            width=1024,
            height=1024,
        )

        encoded = base64.b64encode(b"fake-png-bytes").decode("utf-8")

        with patch(
            "routers.image.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ), patch(
            "routers.image.algo_client.generate_watermarked_image",
            new=AsyncMock(
                return_value={
                    "result_image_base64": encoded,
                    "image_format": "png",
                    "width": 1024,
                    "height": 1024,
                    "elapsed_ms": 1200,
                }
            ),
        ):
            response = await image_router.generate_watermarked_image(
                body=body,
                request=_FakeRequest(),
                authorization="Bearer token-123",
            )

        self.assertIn("image_url", response)
        self.assertIn("download_url", response)
        self.assertEqual(response["watermark_bits"], body.watermark_bits)
        self.assertEqual(response["elapsed_ms"], 1200)

    async def test_generate_watermarked_image_returns_401_without_token(self):
        body = GenerateWatermarkedImageRequest(
            prompt="a cat",
            model="flux2",
            watermark_bits="01010101010101010101010101010101",
            width=1024,
            height=1024,
        )

        with self.assertRaises(HTTPException) as ctx:
            await image_router.generate_watermarked_image(
                body=body,
                request=_FakeRequest(),
                authorization=None,
            )

        self.assertEqual(ctx.exception.status_code, 401)

    async def test_generate_watermarked_image_maps_algo_error(self):
        body = GenerateWatermarkedImageRequest(
            prompt="a cat",
            model="flux2",
            watermark_bits="01010101010101010101010101010101",
            width=1024,
            height=1024,
        )

        with patch(
            "routers.image.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice"}),
        ), patch(
            "routers.image.algo_client.generate_watermarked_image",
            new=AsyncMock(side_effect=AlgoServiceError("算法服务不可达", status_code=503)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await image_router.generate_watermarked_image(
                    body=body,
                    request=_FakeRequest(),
                    authorization="Bearer token-123",
                )

        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
