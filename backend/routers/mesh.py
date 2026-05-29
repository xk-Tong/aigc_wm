import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from config.service_conf import BIZ_MESH_STORAGE_ROOT
from deps import get_current_user
from models.record import WmTaskRecord
from schemas.mesh import (
    ExtractMeshWatermarkResponse,
    GenerateWatermarkedMeshRequest,
    GenerateWatermarkedMeshResponse,
)
from services.algo_client import AlgoServiceError, algo_client
from services.audit_log import log_operation

router = APIRouter(prefix="/api/v1/mesh", tags=["mesh"])


def _resolve_mesh_extension(filename: Optional[str]) -> str:
    valid_extensions = {"obj", "stl", "gltf", "glb"}

    if filename:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix in valid_extensions:
            return suffix

    return "obj"


@router.post(
    "/generate-watermarked",
    response_model=GenerateWatermarkedMeshResponse,
)
async def generate_watermarked_mesh(
    body: GenerateWatermarkedMeshRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成含水印网格模型并返回可访问 URL。"""

    payload = body.model_dump()
    started = perf_counter()
    try:
        mesh_bytes, file_format, algo_elapsed_ms = (
            await algo_client.generate_watermarked_mesh(payload)
        )
    except AlgoServiceError as exc:
        await log_operation(db, user, "embed", "mesh", request, "fail", {"error": exc.message})
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if file_format not in {"obj", "stl", "gltf", "glb"}:
        file_format = "obj"

    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    mesh_id = uuid4().hex

    save_dir = Path(BIZ_MESH_STORAGE_ROOT) / "generated" / date_path / mesh_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"orig.{file_format}"
    file_path = save_dir / file_name
    with file_path.open("wb") as f:
        f.write(mesh_bytes)

    relative_path = file_path.relative_to(Path(BIZ_MESH_STORAGE_ROOT)).as_posix()
    mesh_url = str(request.url_for("storage_mesh", path=relative_path))

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="mesh",
        operation_type="embed",
        watermark_bits=body.watermark_bits,
        prompt=body.prompt,
        model=body.model,
        watermarked_file_url=mesh_url,
        download_url=mesh_url,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=mesh_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "embed", "mesh", request, "success", {"watermark": body.watermark_bits})

    return {
        "mesh_id": mesh_id,
        "mesh_url": mesh_url,
        "download_url": mesh_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "file_format": file_format,
    }


@router.post(
    "/extract-watermark",
    response_model=ExtractMeshWatermarkResponse,
)
async def extract_watermark(
    request: Request,
    mesh_file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """接收用户上传的网格模型文件，提取其中嵌入的 32 位二进制水印。"""

    if not mesh_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的网格模型文件")

    started = perf_counter()

    file_bytes = await mesh_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传的网格模型文件不能为空")

    if len(file_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="网格模型文件大小不能超过 100MB")

    file_format = _resolve_mesh_extension(mesh_file.filename)
    if file_format not in {"obj", "stl", "gltf", "glb"}:
        raise HTTPException(status_code=400, detail="只支持 OBJ、STL、GLTF、GLB 格式网格模型文件")

    extracted_at = datetime.now(timezone.utc)
    date_path = extracted_at.strftime("%Y/%m/%d")
    file_id = uuid4().hex

    save_dir = Path(BIZ_MESH_STORAGE_ROOT) / "uploads" / date_path / file_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / f"source.{file_format}"
    with file_path.open("wb") as f:
        f.write(file_bytes)

    try:
        algo_response = await algo_client.extract_watermark_from_mesh(
            file_name=mesh_file.filename,
            file_bytes=file_bytes,
            content_type=mesh_file.content_type,
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    watermark_bits = str(algo_response.get("extracted_watermark") or "")
    if not re.fullmatch(r"[01]{32}", watermark_bits):
        raise HTTPException(status_code=502, detail="算法服务返回了非法的水印数据")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    record = WmTaskRecord(
        user_id=user["id"],
        username=user["username"],
        media_type="mesh",
        operation_type="extract",
        source_file_name=mesh_file.filename,
        source_file_size=len(file_bytes),
        extracted_bits=watermark_bits,
        elapsed_ms=elapsed_ms,
        status="success",
        file_id=file_id,
    )
    db.add(record)
    await db.commit()
    await log_operation(db, user, "extract", "mesh", request, "success", {"watermark": watermark_bits})

    return {
        "file_id": file_id,
        "file_name": mesh_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
