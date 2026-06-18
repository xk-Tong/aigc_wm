import base64
import binascii
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from config.service_conf import BIZ_IMAGE_STORAGE_ROOT
from deps import get_current_user
from models.record import WmTaskRecord
from schemas.image import (
    ExtractWatermarkResponse,
    GenerateWatermarkedImageRequest,
    GenerateWatermarkedImageResponse,
)
from services.algo_client import AlgoServiceError, algo_client
from services.audit_log import log_operation
from utils.public_url import build_public_url

# 图像业务路由：负责接收前端请求并编排“算法调用 + 文件落盘 + URL 返回”。
router = APIRouter(prefix="/api/v1/image", tags=["image"])


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
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Step 1: 调用算法服务获取生成结果。
    payload = body.model_dump()
    started = perf_counter()
    try:
        algo_response = await algo_client.generate_watermarked_image(payload)
    except AlgoServiceError as exc:
        await log_operation(db, user, "embed", "image", request, "fail", {"error": exc.message})
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
    orig_url = build_public_url(f"/storage/{orig_path.relative_to(storage_root).as_posix()}")
    wm_url = build_public_url(f"/storage/{wm_path.relative_to(storage_root).as_posix()}")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    # Step 6: 写入历史记录。
    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="image",
        operation_type="embed",
        watermark_bits=body.watermark_bits,
        prompt=body.prompt,
        model=body.model,
        original_file_url=orig_url,
        watermarked_file_url=wm_url,
        download_url=wm_url,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=image_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "embed", "image", request, "success", {"watermark": body.watermark_bits})

    # Step 7: 直出业务数据返回给前端。
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
    request: Request,
    image_file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """接收用户上传的图片，提取其中嵌入的 32 位水印。"""

    # Step 1: 读取并校验用户上传的文件。
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

    # Step 6: 写入历史记录。
    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="image",
        operation_type="extract",
        source_file_name=image_file.filename,
        source_file_size=len(file_bytes),
        extracted_bits=watermark_bits,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=file_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "extract", "image", request, "success", {"watermark": watermark_bits})

    # Step 7: 直出给前端需要的结果数据。
    return {
        "file_id": file_id,
        "file_name": image_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
