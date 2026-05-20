import os
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import Response

app = FastAPI(title="Mock 3DGS Algo Service")

# test.ply 文件路径（与本文件同目录）
TEST_PLY_PATH = Path(__file__).parent / "test.ply"


class GenerateGSRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="gaussian-splatting")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    seed: int | None = Field(default=None, ge=0)


def _load_test_ply() -> tuple[bytes, int]:
    """读取 test.ply 文件并返回字节数据和 Gaussian 数量。

    通过解析 PLY 头部的 element vertex 行来获取实际 Gaussian 数量。
    """
    if not TEST_PLY_PATH.exists():
        raise FileNotFoundError(f"test.ply not found at {TEST_PLY_PATH}")

    ply_bytes = TEST_PLY_PATH.read_bytes()

    # 从 PLY 头部解析 Gaussian 数量
    gaussian_count = 0
    header_end = ply_bytes.find(b"end_header")
    if header_end != -1:
        header_text = ply_bytes[:header_end].decode("ascii", errors="ignore")
        for line in header_text.splitlines():
            line = line.strip()
            if line.startswith("element vertex"):
                parts = line.split()
                if len(parts) >= 3:
                    gaussian_count = int(parts[2])
                break

    return ply_bytes, gaussian_count


@app.get("/algo/v1/gs/health")
async def health():
    return {"status": "ok", "service": "mock-gs-algo", "ready": True}


@app.post("/algo/v1/gs/generate")
async def generate(request: GenerateGSRequest):
    """模拟 3DGS 生成接口。

    直接返回 test.ply 文件作为生成结果，通过响应头传递元数据。
    """
    started = perf_counter()

    try:
        ply_bytes, gaussian_count = _load_test_ply()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    elapsed_ms = int((perf_counter() - started) * 1000)

    return Response(
        content=ply_bytes,
        media_type="application/octet-stream",
        headers={
            "X-File-Format": "ply",
            "X-Elapsed-Ms": str(elapsed_ms),
            "X-Gaussian-Count": str(gaussian_count),
        },
    )


@app.post("/algo/v1/gs/watermark/extract")
async def extract_watermark(gs_file: UploadFile = File(...)):
    """模拟提取 3DGS 中的 32 位二进制水印。"""

    started = perf_counter()

    if not gs_file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    file_bytes = await gs_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    watermark_bits = "10101010101010101010101010101010"
    elapsed_ms = int((perf_counter() - started) * 1000)

    return {
        "extracted_watermark": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "echo": {
            "filename": gs_file.filename,
            "content_type": gs_file.content_type,
            "size_bytes": len(file_bytes),
        },
    }
