import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile

from config.service_conf import BIZ_GS_STORAGE_ROOT, GS_REQUIRE_AUTH
from crud import auth as crud_auth
from schemas.gs import (
    ExtractGSWatermarkResponse,
    GenerateWatermarkedGSRequest,
    GenerateWatermarkedGSResponse,
)
from services.algo_client import AlgoServiceError, algo_client

router = APIRouter(prefix="/api/v1/gs", tags=["gs"])


def _extract_token(authorization: Optional[str]) -> Optional[str]:
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
    response_model=GenerateWatermarkedGSResponse,
)
async def generate_watermarked_gs(
    body: GenerateWatermarkedGSRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """生成含水印 3DGS 并返回可访问 URL。"""

    if GS_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    payload = body.model_dump()
    started = perf_counter()
    try:
        gs_bytes, file_format, algo_elapsed_ms, gaussian_count = (
            await algo_client.generate_watermarked_gs(payload)
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if file_format not in {"ply"}:
        file_format = "ply"

    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    gs_id = uuid4().hex

    save_dir = Path(BIZ_GS_STORAGE_ROOT) / "generated" / date_path / gs_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"orig.{file_format}"
    file_path = save_dir / file_name
    with file_path.open("wb") as f:
        f.write(gs_bytes)

    relative_path = file_path.relative_to(Path(BIZ_GS_STORAGE_ROOT)).as_posix()
    gs_url = str(request.url_for("storage_gs", path=relative_path))

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    return {
        "gs_id": gs_id,
        "gs_url": gs_url,
        "download_url": gs_url,
        "watermark_bits": body.watermark_bits,
        "elapsed_ms": elapsed_ms,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": body.model,
        "file_format": file_format,
        "gaussian_count": gaussian_count,
    }


@router.post(
    "/extract-watermark",
    response_model=ExtractGSWatermarkResponse,
)
async def extract_watermark(
    gs_file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
):
    """接收用户上传的 3DGS PLY 文件，提取其中嵌入的 32 位二进制水印。"""

    if GS_REQUIRE_AUTH:
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    if not gs_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的 3DGS PLY 文件")

    file_bytes = await gs_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传的 3DGS 文件不能为空")

    if len(file_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="3DGS 文件大小不能超过 100MB")

    suffix = Path(gs_file.filename).suffix.lower().lstrip(".")
    if suffix not in {"ply"}:
        raise HTTPException(status_code=400, detail="只支持 PLY 格式 3DGS 文件")

    extracted_at = datetime.now(timezone.utc)
    date_path = extracted_at.strftime("%Y/%m/%d")
    file_id = uuid4().hex

    save_dir = Path(BIZ_GS_STORAGE_ROOT) / "uploads" / date_path / file_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / "source.ply"
    with file_path.open("wb") as f:
        f.write(file_bytes)

    started = perf_counter()
    try:
        algo_response = await algo_client.extract_watermark_from_gs(
            file_name=gs_file.filename,
            file_bytes=file_bytes,
            content_type=gs_file.content_type,
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    watermark_bits = str(algo_response.get("extracted_watermark") or "")
    if not re.fullmatch(r"[01]{32}", watermark_bits):
        raise HTTPException(status_code=502, detail="算法服务返回了非法的水印数据")

    elapsed_ms = int(algo_response.get("elapsed_ms") or ((perf_counter() - started) * 1000))

    return {
        "file_id": file_id,
        "file_name": gs_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
