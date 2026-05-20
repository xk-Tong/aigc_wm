from typing import Any

import httpx

from config.service_conf import (
    ALGO_IMAGE_API_KEY,
    ALGO_IMAGE_BASE_URL,
    ALGO_IMAGE_TIMEOUT_SECONDS,
    ALGO_GS_API_KEY,
    ALGO_GS_BASE_URL,
    ALGO_GS_TIMEOUT_SECONDS,
    ALGO_MESH_API_KEY,
    ALGO_MESH_BASE_URL,
    ALGO_MESH_TIMEOUT_SECONDS,
    ALGO_POINTCLOUD_API_KEY,
    ALGO_POINTCLOUD_BASE_URL,
    ALGO_POINTCLOUD_TIMEOUT_SECONDS,
)


class AlgoServiceError(Exception):
    """统一封装算法服务错误，便于路由层直接映射 HTTP 状态码。"""

    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AlgoClient:
    """算法服务 HTTP 客户端。

    用法场景：业务后端需要把前端请求转发给算法服务时调用该类。
    """

    async def generate_watermarked_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用算法服务的生成接口。

        参数:
            payload: 发送给算法服务的请求 JSON。

        返回:
            算法服务返回的 JSON 字典，至少包含 result_image_base64。

        异常:
            AlgoServiceError: 当算法服务超时、不可达或返回格式异常时抛出。
        """
        headers = {}
        # 可选服务间鉴权头：只有配置了 API Key 才会附带。
        if ALGO_IMAGE_API_KEY:
            headers["X-API-Key"] = ALGO_IMAGE_API_KEY

        try:
            # 使用异步 HTTP 客户端避免阻塞主线程。
            async with httpx.AsyncClient(timeout=ALGO_IMAGE_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_IMAGE_BASE_URL}/algo/v1/generate",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            # 超时一般是算法处理太慢或网络波动。
            raise AlgoServiceError("算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            # 请求都发不出去，通常是地址不可达或服务未启动。
            raise AlgoServiceError("算法服务不可达", status_code=503) from exc

        # 5xx 视为算法服务内部异常。
        if response.status_code >= 500:
            raise AlgoServiceError("算法服务执行失败", status_code=502)

        # 4xx 通常是参数问题，尽量提取算法服务返回的具体信息。
        if response.status_code >= 400:
            detail = "算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        try:
            data = response.json()
        except ValueError as exc:
            raise AlgoServiceError("算法服务返回了非 JSON 数据", status_code=502) from exc

        # 主链路依赖 original_image_base64 和 watermarked_image_base64 两个字段。
        if not isinstance(data, dict) or not data.get("original_image_base64") or not data.get("watermarked_image_base64"):
            raise AlgoServiceError("算法服务响应缺少 original_image_base64 或 watermarked_image_base64 字段", status_code=502)

        return data

    async def extract_watermark_from_image(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """调用算法服务的提取接口。

        参数:
            file_name: 上传文件名，用于传给算法服务做日志和排查。
            file_bytes: 图片二进制内容。
            content_type: 图片 MIME 类型，例如 image/png。

        返回:
            算法服务返回的 JSON 字典，至少包含 extracted_watermark。
        """

        headers = {}
        if ALGO_IMAGE_API_KEY:
            headers["X-API-Key"] = ALGO_IMAGE_API_KEY

        files = {
            "image_file": (
                file_name,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }

        try:
            async with httpx.AsyncClient(timeout=ALGO_IMAGE_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_IMAGE_BASE_URL}/algo/v1/watermark/extract",
                    files=files,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        try:
            data = response.json()
        except ValueError as exc:
            raise AlgoServiceError("算法服务返回了非 JSON 数据", status_code=502) from exc

        if not isinstance(data, dict):
            raise AlgoServiceError("算法服务返回了非法数据格式", status_code=502)

        extracted_watermark = data.get("extracted_watermark") or data.get("watermark_bits")
        if not extracted_watermark:
            raise AlgoServiceError("算法服务响应缺少 extracted_watermark 字段", status_code=502)

        data["extracted_watermark"] = extracted_watermark
        return data

    async def generate_watermarked_pointcloud(
        self, payload: dict[str, Any]
    ) -> tuple[bytes, str, int]:
        """调用点云算法服务的生成接口，返回二进制点云文件。

        参数:
            payload: 发送给算法服务的请求 JSON。

        返回:
            (pointcloud_bytes, file_format, algo_elapsed_ms)
            - pointcloud_bytes: 点云文件的二进制内容。
            - file_format: 文件格式，如 "ply"。
            - algo_elapsed_ms: 算法端耗时（毫秒）。

        异常:
            AlgoServiceError: 当算法服务超时、不可达或返回格式异常时抛出。
        """
        headers = {}
        if ALGO_POINTCLOUD_API_KEY:
            headers["X-API-Key"] = ALGO_POINTCLOUD_API_KEY

        try:
            async with httpx.AsyncClient(timeout=ALGO_POINTCLOUD_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_POINTCLOUD_BASE_URL}/algo/v1/pointcloud/generate",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("点云算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("点云算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("点云算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "点云算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        pointcloud_bytes = response.content
        if not pointcloud_bytes:
            raise AlgoServiceError("点云算法服务返回了空数据", status_code=502)

        file_format = (response.headers.get("X-File-Format") or "ply").lower()
        algo_elapsed_ms = int(response.headers.get("X-Elapsed-Ms", "0"))

        return pointcloud_bytes, file_format, algo_elapsed_ms

    async def extract_watermark_from_pointcloud(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """调用点云算法服务的水印提取接口。

        参数:
            file_name: 上传文件名。
            file_bytes: 点云文件二进制内容。
            content_type: 文件 MIME 类型。

        返回:
            算法服务返回的 JSON 字典，至少包含 extracted_watermark。
        """
        headers = {}
        if ALGO_POINTCLOUD_API_KEY:
            headers["X-API-Key"] = ALGO_POINTCLOUD_API_KEY

        files = {
            "pointcloud_file": (
                file_name,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }

        try:
            async with httpx.AsyncClient(timeout=ALGO_POINTCLOUD_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_POINTCLOUD_BASE_URL}/algo/v1/pointcloud/watermark/extract",
                    files=files,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("点云算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("点云算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("点云算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "点云算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        try:
            data = response.json()
        except ValueError as exc:
            raise AlgoServiceError("点云算法服务返回了非 JSON 数据", status_code=502) from exc

        if not isinstance(data, dict):
            raise AlgoServiceError("点云算法服务返回了非法数据格式", status_code=502)

        extracted_watermark = data.get("extracted_watermark") or data.get("watermark_bits")
        if not extracted_watermark:
            raise AlgoServiceError("点云算法服务响应缺少 extracted_watermark 字段", status_code=502)

        data["extracted_watermark"] = extracted_watermark
        return data


    async def generate_watermarked_mesh(
        self, payload: dict[str, Any]
    ) -> tuple[bytes, str, int]:
        """调用网格算法服务的生成接口，返回二进制网格文件。

        返回:
            (mesh_bytes, file_format, algo_elapsed_ms)
        """
        headers = {}
        if ALGO_MESH_API_KEY:
            headers["X-API-Key"] = ALGO_MESH_API_KEY

        try:
            async with httpx.AsyncClient(timeout=ALGO_MESH_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_MESH_BASE_URL}/algo/v1/mesh/generate",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("网格算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("网格算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("网格算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "网格算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        mesh_bytes = response.content
        if not mesh_bytes:
            raise AlgoServiceError("网格算法服务返回了空数据", status_code=502)

        file_format = (response.headers.get("X-File-Format") or "obj").lower()
        algo_elapsed_ms = int(response.headers.get("X-Elapsed-Ms", "0"))

        return mesh_bytes, file_format, algo_elapsed_ms

    async def extract_watermark_from_mesh(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """调用网格算法服务的水印提取接口。"""
        headers = {}
        if ALGO_MESH_API_KEY:
            headers["X-API-Key"] = ALGO_MESH_API_KEY

        files = {
            "mesh_file": (
                file_name,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }

        try:
            async with httpx.AsyncClient(timeout=ALGO_MESH_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_MESH_BASE_URL}/algo/v1/mesh/watermark/extract",
                    files=files,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("网格算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("网格算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("网格算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "网格算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        try:
            data = response.json()
        except ValueError as exc:
            raise AlgoServiceError("网格算法服务返回了非 JSON 数据", status_code=502) from exc

        if not isinstance(data, dict):
            raise AlgoServiceError("网格算法服务返回了非法数据格式", status_code=502)

        extracted_watermark = data.get("extracted_watermark") or data.get("watermark_bits")
        if not extracted_watermark:
            raise AlgoServiceError("网格算法服务响应缺少 extracted_watermark 字段", status_code=502)

        data["extracted_watermark"] = extracted_watermark
        return data

    async def generate_watermarked_gs(
        self, payload: dict[str, Any]
    ) -> tuple[bytes, str, int, int]:
        """调用 3DGS 算法服务的生成接口，返回二进制 PLY 文件。

        返回:
            (gs_bytes, file_format, algo_elapsed_ms, gaussian_count)
        """
        headers = {}
        if ALGO_GS_API_KEY:
            headers["X-API-Key"] = ALGO_GS_API_KEY

        try:
            async with httpx.AsyncClient(timeout=ALGO_GS_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_GS_BASE_URL}/algo/v1/gs/generate",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("3DGS算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("3DGS算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("3DGS算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "3DGS算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        gs_bytes = response.content
        if not gs_bytes:
            raise AlgoServiceError("3DGS算法服务返回了空数据", status_code=502)

        file_format = (response.headers.get("X-File-Format") or "ply").lower()
        algo_elapsed_ms = int(response.headers.get("X-Elapsed-Ms", "0"))
        gaussian_count = int(response.headers.get("X-Gaussian-Count", "0"))

        return gs_bytes, file_format, algo_elapsed_ms, gaussian_count

    async def extract_watermark_from_gs(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """调用 3DGS 算法服务的水印提取接口。"""
        headers = {}
        if ALGO_GS_API_KEY:
            headers["X-API-Key"] = ALGO_GS_API_KEY

        files = {
            "gs_file": (
                file_name,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }

        try:
            async with httpx.AsyncClient(timeout=ALGO_GS_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{ALGO_GS_BASE_URL}/algo/v1/gs/watermark/extract",
                    files=files,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise AlgoServiceError("3DGS算法服务响应超时", status_code=503) from exc
        except httpx.RequestError as exc:
            raise AlgoServiceError("3DGS算法服务不可达", status_code=503) from exc

        if response.status_code >= 500:
            raise AlgoServiceError("3DGS算法服务执行失败", status_code=502)

        if response.status_code >= 400:
            detail = "3DGS算法服务参数错误"
            try:
                payload_data = response.json()
                detail = payload_data.get("detail") or payload_data.get("message") or detail
            except Exception:
                pass
            raise AlgoServiceError(detail, status_code=422)

        try:
            data = response.json()
        except ValueError as exc:
            raise AlgoServiceError("3DGS算法服务返回了非 JSON 数据", status_code=502) from exc

        if not isinstance(data, dict):
            raise AlgoServiceError("3DGS算法服务返回了非法数据格式", status_code=502)

        extracted_watermark = data.get("extracted_watermark") or data.get("watermark_bits")
        if not extracted_watermark:
            raise AlgoServiceError("3DGS算法服务响应缺少 extracted_watermark 字段", status_code=502)

        data["extracted_watermark"] = extracted_watermark
        return data


# 提供模块级单例，方便路由直接复用。
algo_client = AlgoClient()
