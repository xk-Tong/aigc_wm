from typing import Any

import httpx

from config.service_conf import (
    ALGO_IMAGE_API_KEY,
    ALGO_IMAGE_BASE_URL,
    ALGO_IMAGE_TIMEOUT_SECONDS,
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

        # 主链路依赖 result_image_base64 字段，这里做强校验。
        if not isinstance(data, dict) or not data.get("result_image_base64"):
            raise AlgoServiceError("算法服务响应缺少 result_image_base64 字段", status_code=502)

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


# 提供模块级单例，方便路由直接复用。
algo_client = AlgoClient()
