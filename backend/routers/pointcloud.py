import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile

from config.service_conf import BIZ_POINTCLOUD_STORAGE_ROOT, POINTCLOUD_REQUIRE_AUTH
from crud import auth as crud_auth
from schemas.pointcloud import (
    ExtractPointcloudWatermarkResponse,
    GenerateWatermarkedPointcloudRequest,
    GenerateWatermarkedPointcloudResponse,
)
from services.algo_client import AlgoServiceError, algo_client

router = APIRouter(prefix="/api/v1/pointcloud", tags=["pointcloud"])


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    value = authorization.strip()
    if not value:
        return None

    if value.lower().startswith("bearer "):
        value = value[7:].strip()

    return value or None


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
    authorization: Optional[str] = Header(default=None),
):
    """生成含水印点云并返回可访问 URL。"""

    if POINTCLOUD_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    payload = body.model_dump()
    started = perf_counter()
    try:
        pointcloud_bytes, point_count, file_format, algo_elapsed_ms = (
            await algo_client.generate_watermarked_pointcloud(payload)
        )
    except AlgoServiceError as exc:
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
    pointcloud_url = str(request.url_for("storage_pointcloud", path=relative_path))

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    actual_point_count = point_count if point_count > 0 else body.point_count

    return {
        "pointcloud_id": pointcloud_id,
        "pointcloud_url": pointcloud_url,
        "download_url": pointcloud_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "point_count": actual_point_count,
        "file_format": file_format,
    }


@router.post(
    "/extract-watermark",
    response_model=ExtractPointcloudWatermarkResponse,
)
async def extract_watermark(
    pointcloud_file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
):
    """接收用户上传的点云文件，提取其中嵌入的 6 位十六进制水印。"""

    if POINTCLOUD_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    if not pointcloud_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的点云文件")

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

    started = perf_counter()
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

    elapsed_ms = int(algo_response.get("elapsed_ms") or ((perf_counter() - started) * 1000))

    return {
        "file_id": file_id,
        "file_name": pointcloud_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
