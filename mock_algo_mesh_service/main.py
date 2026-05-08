from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import Response

app = FastAPI(title="Mock Mesh Algo Service")


class GenerateMeshRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="trellis")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    seed: int | None = Field(default=None, ge=0)


def _generate_mock_obj_bytes() -> bytes:
    """生成一个简单的 OBJ 格式立方体作为模拟网格数据。

    8 个顶点，6 个四边形面（共 12 个三角形面）。
    替换为此函数即可接入真实网格生成模型。
    """
    vertices = [
        "v -0.5 -0.5  0.5",
        "v  0.5 -0.5  0.5",
        "v -0.5  0.5  0.5",
        "v  0.5  0.5  0.5",
        "v -0.5  0.5 -0.5",
        "v  0.5  0.5 -0.5",
        "v -0.5 -0.5 -0.5",
        "v  0.5 -0.5 -0.5",
    ]
    faces = [
        "f 1 2 4 3",
        "f 3 4 6 5",
        "f 5 6 8 7",
        "f 7 8 2 1",
        "f 2 8 6 4",
        "f 7 1 3 5",
    ]
    obj_content = "\n".join(vertices) + "\n" + "\n".join(faces) + "\n"
    return obj_content.encode("ascii")


@app.get("/algo/v1/mesh/health")
async def health():
    return {"status": "ok", "service": "mock-mesh-algo", "ready": True}


@app.post("/algo/v1/mesh/generate")
async def generate(request: GenerateMeshRequest):
    """模拟网格生成接口。

    返回二进制 OBJ 文件流，通过响应头传递元数据。
    """
    started = perf_counter()

    obj_bytes = _generate_mock_obj_bytes()

    elapsed_ms = int((perf_counter() - started) * 1000)

    return Response(
        content=obj_bytes,
        media_type="application/octet-stream",
        headers={
            "X-File-Format": "obj",
            "X-Elapsed-Ms": str(elapsed_ms),
        },
    )


@app.post("/algo/v1/mesh/watermark/extract")
async def extract_watermark(mesh_file: UploadFile = File(...)):
    """模拟提取网格模型中的 32 位二进制水印。"""

    started = perf_counter()

    if not mesh_file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    file_bytes = await mesh_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    watermark_bits = "10101010101010101010101010101010"
    elapsed_ms = int((perf_counter() - started) * 1000)

    return {
        "extracted_watermark": watermark_bits,
        "elapsed_ms": elapsed_ms,
        "echo": {
            "filename": mesh_file.filename,
            "content_type": mesh_file.content_type,
            "size_bytes": len(file_bytes),
        },
    }
