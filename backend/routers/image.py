import base64
import binascii
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request

from config.service_conf import BIZ_IMAGE_STORAGE_ROOT, IMAGE_REQUIRE_AUTH
from crud import auth as crud_auth
from schemas.image import GenerateWatermarkedImageRequest, GenerateWatermarkedImageResponse
from services.algo_client import AlgoServiceError, algo_client

# 图像业务路由：负责接收前端请求并编排“算法调用 + 文件落盘 + URL 返回”。
router = APIRouter(prefix="/api/v1/image", tags=["image"])


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    """从 Authorization 请求头中提取 token。

    支持两种输入：
    1) "Bearer xxx"
    2) 直接传 "xxx"
    """
    if not authorization:
        return None

    value = authorization.strip()
    if not value:
        return None

    if value.lower().startswith("bearer "):
        value = value[7:].strip()

    return value or None


@router.post(
    "/generate-watermarked",
    response_model=GenerateWatermarkedImageResponse,
)
async def generate_watermarked_image(
    body: GenerateWatermarkedImageRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """生成含水印图像并返回可访问 URL。

    参数:
        body: 前端提交的生成参数（提示词、模型、水印等）。
        request: FastAPI 请求对象，用于拼接静态资源 URL。
        authorization: 可选认证头，开启鉴权时必填。

    返回:
        GenerateWatermarkedImageResponse 对应的字典数据。
    """

    # Step 1: 可选鉴权（联调可通过配置关闭）。
    if IMAGE_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    # Step 2: 调用算法服务获取生成结果。
    payload = body.model_dump()
    started = perf_counter()
    try:
        algo_response = await algo_client.generate_watermarked_image(payload)
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # Step 3: 解析算法服务返回的图片数据。
    image_base64 = algo_response.get("result_image_base64", "")
    image_format = (algo_response.get("image_format") or "png").lower()
    if image_format not in {"png", "jpg", "jpeg", "webp"}:
        image_format = "png"

    image_bytes: bytes
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=502, detail="算法服务返回了非法图像数据") from exc

    # Step 4: 生成按日期分层的目录，把图片写入业务后端磁盘。
    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    image_id = uuid4().hex

    save_dir = Path(BIZ_IMAGE_STORAGE_ROOT) / "generated" / date_path / image_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"orig.{image_format}"
    file_path = save_dir / file_name
    with file_path.open("wb") as f:
        f.write(image_bytes)

    # Step 5: 把磁盘相对路径转换为前端可直接访问的 URL。
    relative_path = file_path.relative_to(Path(BIZ_IMAGE_STORAGE_ROOT)).as_posix()
    image_url = str(request.url_for("storage", path=relative_path))

    # 如果算法侧没有给耗时，这里用本地统计值兜底。
    elapsed_ms = int(algo_response.get("elapsed_ms") or ((perf_counter() - started) * 1000))

    # Step 6: 直出业务数据返回给前端。
    return {
        "image_id": image_id,
        "image_url": image_url,
        "download_url": image_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "width": int(algo_response.get("width") or body.width),
        "height": int(algo_response.get("height") or body.height),
    }
