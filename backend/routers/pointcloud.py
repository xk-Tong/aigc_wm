import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from config.service_conf import BIZ_POINTCLOUD_STORAGE_ROOT
from deps import get_current_user
from models.record import WmTaskRecord
from schemas.pointcloud import (
    ExtractPointcloudWatermarkResponse,
    GenerateWatermarkedPointcloudRequest,
    GenerateWatermarkedPointcloudResponse,
)
from services.algo_client import AlgoServiceError, algo_client
from services.audit_log import log_operation
from utils.public_url import build_public_url

router = APIRouter(prefix="/api/v1/pointcloud", tags=["pointcloud"])


def _resolve_pointcloud_extension(filename: Optional[str]) -> str:
    valid_extensions = {"ply", "pcd", "xyz", "obj", "stl"}

    if filename:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix in valid_extensions:
            return suffix

    return "ply"


@router.post(
    "/generate-watermarked",
    response_model=GenerateWatermarkedPointcloudResponse,
)
async def generate_watermarked_pointcloud(
    body: GenerateWatermarkedPointcloudRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成含水印点云并返回可访问 URL。"""

    payload = body.model_dump()
    started = perf_counter()
    try:
        pointcloud_bytes, file_format, algo_elapsed_ms = (
            await algo_client.generate_watermarked_pointcloud(payload)
        )
    except AlgoServiceError as exc:
        await log_operation(db, user, "embed", "pointcloud", request, "fail", {"error": exc.message})
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if file_format not in {"ply", "pcd", "xyz", "obj", "stl"}:
        file_format = "ply"

    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    pointcloud_id = uuid4().hex

    save_dir = Path(BIZ_POINTCLOUD_STORAGE_ROOT) / "generated" / date_path / pointcloud_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"orig.{file_format}"
    file_path = save_dir / file_name
    with file_path.open("wb") as f:
        f.write(pointcloud_bytes)

    relative_path = file_path.relative_to(Path(BIZ_POINTCLOUD_STORAGE_ROOT)).as_posix()
    pointcloud_url = build_public_url(f"/storage_pointcloud/{relative_path}")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="pointcloud",
        operation_type="embed",
        watermark_bits=body.watermark_bits,
        prompt=body.prompt,
        model=body.model,
        watermarked_file_url=pointcloud_url,
        download_url=pointcloud_url,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=pointcloud_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "embed", "pointcloud", request, "success", {"watermark": body.watermark_bits})

    return {
        "pointcloud_id": pointcloud_id,
        "pointcloud_url": pointcloud_url,
        "download_url": pointcloud_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "file_format": file_format,
    }


@router.post(
    "/extract-watermark",
    response_model=ExtractPointcloudWatermarkResponse,
)
async def extract_watermark(
    request: Request,
    pointcloud_file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """接收用户上传的点云文件，提取其中嵌入的 6 位十六进制水印。"""

    if not pointcloud_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的点云文件")

    started = perf_counter()

    file_bytes = await pointcloud_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传的点云文件不能为空")

    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="点云文件大小不能超过 50MB")

    file_format = _resolve_pointcloud_extension(pointcloud_file.filename)
    if file_format not in {"ply", "pcd", "xyz", "obj", "stl"}:
        raise HTTPException(status_code=400, detail="只支持 PLY、PCD、XYZ、OBJ、STL 格式点云文件")

    extracted_at = datetime.now(timezone.utc)
    date_path = extracted_at.strftime("%Y/%m/%d")
    file_id = uuid4().hex

    save_dir = Path(BIZ_POINTCLOUD_STORAGE_ROOT) / "uploads" / date_path / file_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / f"source.{file_format}"
    with file_path.open("wb") as f:
        f.write(file_bytes)

    try:
        algo_response = await algo_client.extract_watermark_from_pointcloud(
            file_name=pointcloud_file.filename,
            file_bytes=file_bytes,
            content_type=pointcloud_file.content_type,
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    watermark_bits = str(algo_response.get("extracted_watermark") or "")
    if not re.fullmatch(r"[0-9A-Fa-f]{8}", watermark_bits):
        raise HTTPException(status_code=502, detail="算法服务返回了非法的水印数据")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="pointcloud",
        operation_type="extract",
        source_file_name=pointcloud_file.filename,
        source_file_size=len(file_bytes),
        extracted_bits=watermark_bits,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=file_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "extract", "pointcloud", request, "success", {"watermark": watermark_bits})

    return {
        "file_id": file_id,
        "file_name": pointcloud_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
