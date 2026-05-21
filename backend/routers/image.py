import base64
import binascii
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile

from config.service_conf import BIZ_IMAGE_STORAGE_ROOT, IMAGE_REQUIRE_AUTH
from crud import auth as crud_auth
from schemas.image import (
    ExtractWatermarkResponse,
    GenerateWatermarkedImageRequest,
    GenerateWatermarkedImageResponse,
)
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


def _resolve_image_extension(filename: Optional[str], content_type: Optional[str]) -> str:
    """根据文件名或 MIME 类型，推断一个可保存的图片后缀。"""

    content_type_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }

    if filename:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if suffix == "jpeg" else suffix

    if content_type and content_type in content_type_map:
        return content_type_map[content_type]

    return "png"


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

    # Step 3: 解析算法服务返回的两张图片（原图 + 水印图）。
    orig_base64 = algo_response.get("original_image_base64", "")
    wm_base64 = algo_response.get("watermarked_image_base64", "")
    image_format = (algo_response.get("image_format") or "png").lower()
    if image_format not in {"png", "jpg", "jpeg", "webp"}:
        image_format = "png"

    orig_bytes: bytes
    wm_bytes: bytes
    try:
        orig_bytes = base64.b64decode(orig_base64, validate=True)
        wm_bytes = base64.b64decode(wm_base64, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=502, detail="算法服务返回了非法图像数据") from exc

    # Step 4: 生成按日期分层的目录，把两张图片写入业务后端磁盘。
    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    image_id = uuid4().hex

    save_dir = Path(BIZ_IMAGE_STORAGE_ROOT) / "generated" / date_path / image_id
    save_dir.mkdir(parents=True, exist_ok=True)

    orig_path = save_dir / f"orig.{image_format}"
    wm_path = save_dir / f"wm.{image_format}"
    orig_path.write_bytes(orig_bytes)
    wm_path.write_bytes(wm_bytes)

    # Step 5: 把磁盘相对路径转换为前端可直接访问的 URL。
    storage_root = Path(BIZ_IMAGE_STORAGE_ROOT)
    orig_url = str(request.url_for("storage", path=orig_path.relative_to(storage_root).as_posix()))
    wm_url = str(request.url_for("storage", path=wm_path.relative_to(storage_root).as_posix()))

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    # Step 6: 直出业务数据返回给前端。
    return {
        "image_id": image_id,
        "original_image_url": orig_url,
        "watermarked_image_url": wm_url,
        "download_url": wm_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "width": int(algo_response.get("width") or body.width),
        "height": int(algo_response.get("height") or body.height),
    }


@router.post(
    "/extract-watermark",
    response_model=ExtractWatermarkResponse,
)
async def extract_watermark(
    image_file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
):
    """接收用户上传的图片，提取其中嵌入的 32 位水印。"""

    # Step 1: 可选鉴权。
    if IMAGE_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    # Step 2: 读取并校验用户上传的文件。
    if not image_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的图像文件")

    started = perf_counter()

    file_bytes = await image_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传的图像不能为空")

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图像大小不能超过 10MB")

    image_format = _resolve_image_extension(image_file.filename, image_file.content_type)
    if image_format not in {"png", "jpg", "webp"}:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、WEBP 格式图像")

    # Step 3: 先把上传文件保存到业务后端磁盘，方便审计和后续排查。
    extracted_at = datetime.now(timezone.utc)
    date_path = extracted_at.strftime("%Y/%m/%d")
    file_id = uuid4().hex

    save_dir = Path(BIZ_IMAGE_STORAGE_ROOT) / "uploads" / date_path / file_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / f"source.{image_format}"
    with file_path.open("wb") as f:
        f.write(file_bytes)

    # Step 4: 调用算法服务提取水印。
    try:
        algo_response = await algo_client.extract_watermark_from_image(
            file_name=image_file.filename,
            file_bytes=file_bytes,
            content_type=image_file.content_type,
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # Step 5: 校验提取结果，确保返回的是 32 位二进制字符串。
    watermark_bits = str(algo_response.get("extracted_watermark") or "")
    if not re.fullmatch(r"[01]{32}", watermark_bits):
        raise HTTPException(status_code=502, detail="算法服务返回了非法的水印数据")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    # Step 6: 直出给前端需要的结果数据。
    return {
        "file_id": file_id,
        "file_name": image_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
