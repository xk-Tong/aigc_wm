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


# 3DGS 模块和图像/点云/网格保持同样的两条主链路：生成和提取。
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
        # 3DGS 生成默认走登录态校验，避免未登录用户直接占用后端算力和磁盘。
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    # 先把 Pydantic 请求体转成普通 dict，再交给算法客户端转发。
    payload = body.model_dump()
    started = perf_counter()
    try:
        gs_bytes, file_format, algo_elapsed_ms, gaussian_count = (
            await algo_client.generate_watermarked_gs(payload)
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    # 当前前端预览和提取流程都只接受 PLY，因此统一兜底到 ply。
    if file_format not in {"ply"}:
        file_format = "ply"

    generated_at = datetime.now(timezone.utc)
    date_path = generated_at.strftime("%Y/%m/%d")
    gs_id = uuid4().hex

    # 按日期 + UUID 分层存储，便于排查和离线清理。
    save_dir = Path(BIZ_GS_STORAGE_ROOT) / "generated" / date_path / gs_id
    save_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"orig.{file_format}"
    file_path = save_dir / file_name
    with file_path.open("wb") as f:
        f.write(gs_bytes)

    # 前端直接使用可访问 URL 做 3D 预览和下载。
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
        # 提取接口和生成接口一致，也走登录态校验。
        token = _extract_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
        if not session_data:
            raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    if not gs_file.filename:
        raise HTTPException(status_code=400, detail="请上传有效的 3DGS PLY 文件")

    started = perf_counter()

    file_bytes = await gs_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传的 3DGS 文件不能为空")

    if len(file_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="3DGS 文件大小不能超过 100MB")

    # 只支持 PLY，和前端上传限制、算法服务约定保持一致。
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

    # 先落盘，再转发给算法服务，保证上传文件在服务端有完整留痕。
    try:
        algo_response = await algo_client.extract_watermark_from_gs(
            file_name=gs_file.filename,
            file_bytes=file_bytes,
            content_type=gs_file.content_type,
        )
    except AlgoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    watermark_bits = str(algo_response.get("extracted_watermark") or "")
    # 算法服务必须返回 32 位二进制串，前端后续会转回十六进制展示。
    if not re.fullmatch(r"[01]{32}", watermark_bits):
        raise HTTPException(status_code=502, detail="算法服务返回了非法的水印数据")

    local_elapsed_ms = int((perf_counter() - started) * 1000)
    algo_elapsed_ms = int(algo_response.get("elapsed_ms") or 0)
    elapsed_ms = max(local_elapsed_ms, algo_elapsed_ms)

    return {
        "file_id": file_id,
        "file_name": gs_file.filename,
        "watermark_bits": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_size_bytes": len(file_bytes),
    }
