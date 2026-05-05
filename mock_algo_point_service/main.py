import struct
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import Response

app = FastAPI(title="Mock Point Cloud Algo Service")


class GeneratePointcloudRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="trellis")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    point_count: int = Field(default=50000, ge=1000, le=1000000)


def _generate_mock_ply_bytes(point_count: int) -> bytes:
    """生成一个简单的 PLY 格式点云二进制数据。

    生成球体表面随机点，使用 binary_little_endian 格式以减小体积。
    """
    import math
    import random

    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {point_count}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    )

    vertex_data = bytearray()
    for _ in range(point_count):
        theta = random.random() * 2 * math.pi
        phi = math.acos(2 * random.random() - 1)
        radius = 1.5 + (random.random() * 0.1)

        x = radius * math.sin(phi) * math.cos(theta)
        y = radius * math.sin(phi) * math.sin(theta)
        z = radius * math.cos(phi)

        r = int(((y / radius + 1) / 2) * 128 + 127)
        g = int(((z / radius + 1) / 2) * 128 + 80)
        b = int(((x / radius + 1) / 2) * 128 + 60)

        vertex_data += struct.pack("<fffBBB", x, y, z, r, g, b)

    return header.encode("ascii") + bytes(vertex_data)


@app.get("/algo/v1/pointcloud/health")
async def health():
    return {"status": "ok", "service": "mock-pointcloud-algo", "ready": True}


@app.post("/algo/v1/pointcloud/generate")
async def generate(request: GeneratePointcloudRequest):
    """模拟点云生成接口。

    返回二进制 PLY 文件流，通过响应头传递元数据。
    """
    started = perf_counter()

    point_count = min(request.point_count, 100000)
    ply_bytes = _generate_mock_ply_bytes(point_count)

    elapsed_ms = int((perf_counter() - started) * 1000)

    return Response(
        content=ply_bytes,
        media_type="application/octet-stream",
        headers={
            "X-Point-Count": str(point_count),
            "X-File-Format": "ply",
            "X-Elapsed-Ms": str(elapsed_ms),
        },
    )


@app.post("/algo/v1/pointcloud/watermark/extract")
async def extract_watermark(pointcloud_file: UploadFile = File(...)):
    """模拟提取点云中的 32 位水印。"""

    started = perf_counter()

    if not pointcloud_file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    file_bytes = await pointcloud_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    watermark_bits = "01010101010101010101010101010101"
    elapsed_ms = int((perf_counter() - started) * 1000)

    return {
        "extracted_watermark": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "echo": {
            "filename": pointcloud_file.filename,
            "content_type": pointcloud_file.content_type,
            "size_bytes": len(file_bytes),
        },
    }
