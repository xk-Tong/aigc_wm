import os
import tempfile
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import Response

# 引入水印核心类
from core import GS3DWatermark

app = FastAPI(title="Mock 3DGS Algo Service")

# test.ply 文件路径（与本文件同目录）
TEST_PLY_PATH = Path(__file__).parent / "test.ply"


class GenerateGSRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="gaussian-splatting")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    seed: int | None = Field(default=None, ge=0)


def _load_test_ply_with_watermark(watermark_bits: str) -> tuple[bytes, int]:
    """读取 test.ply 文件，调用核心算法嵌入水印后返回字节数据和 Gaussian 数量。"""
    if not TEST_PLY_PATH.exists():
        raise FileNotFoundError(f"test.ply not found at {TEST_PLY_PATH}")

    # 将32位二进制字符串转换为核心代码需要的无符号整数载荷
    payload = int(watermark_bits, 2)
    watermarker = GS3DWatermark()
    
    # 创建临时文件用于存储加水印后的输出
    with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp_file:
        tmp_out_path = tmp_file.name

    try:
        # 执行水印嵌入
        watermarker.embed(str(TEST_PLY_PATH), tmp_out_path, payload)
        
        # 读取带有水印的新文件内容
        ply_bytes = Path(tmp_out_path).read_bytes()

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
    finally:
        # 确保清理临时文件
        if os.path.exists(tmp_out_path):
            os.remove(tmp_out_path)


def _extract_watermark_from_bytes(file_bytes: bytes) -> str:
    """将上传的文件字节流写入临时文件，提取水印并转换为二进制字符串。"""
    watermarker = GS3DWatermark()
    
    with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:
        # 提取整型载荷
        payload = watermarker.extract(tmp_path)
        # 将整型格式化回32位二进制字符串，高位补零
        return format(payload, '032b')
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/algo/v1/gs/health")
async def health():
    return {"status": "ok", "service": "mock-gs-algo", "ready": True}


@app.post("/algo/v1/gs/generate")
async def generate(request: GenerateGSRequest):
    """3DGS 生成接口。"""
    started = perf_counter()

    try:
        # 将前端请求中的水印二进制字符串传入处理函数
        ply_bytes, gaussian_count = _load_test_ply_with_watermark(request.watermark_bits)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"水印嵌入失败: {str(e)}")

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
    """提取 3DGS 中的 32 位二进制水印。"""
    started = perf_counter()

    if not gs_file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    file_bytes = await gs_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    try:
        # 调用提取封装函数
        watermark_bits = _extract_watermark_from_bytes(file_bytes)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"水印提取失败: {str(e)}")
         
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