import base64
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 该服务用于本地联调：模拟算法后端，不做真实模型推理。
app = FastAPI(title="Mock Algo Service")


class GenerateRequest(BaseModel):
    """模拟算法服务的生成请求体。"""

    # 与业务后端约定的字段保持一致，便于验证对接是否正确。
    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="flux2")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    width: int = Field(default=2048)
    height: int = Field(default=2048)
    guidance_scale: float = Field(default=1.0)


def _load_test_image_base64() -> str:
    """读取项目根目录 test.png，并转成 base64 字符串返回。"""
    project_root = Path(__file__).resolve().parents[1]
    image_path = project_root / "test.png"

    if not image_path.exists():
        raise FileNotFoundError(f"未找到测试图片: {image_path}")

    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


@app.get("/algo/v1/health")
async def health():
    # 健康检查接口：用于确认模拟算法服务是否存活。
    return {"status": "ok", "service": "mock-algo", "ready": True}


@app.post("/algo/v1/generate")
async def generate(request: GenerateRequest):
    """模拟图像生成接口。

    参数:
        request: 业务后端转发过来的生成参数。

    返回:
        与真实算法服务相同结构的 JSON，包含 result_image_base64。
    """

    # 记录耗时，便于业务后端展示“生成时间”。
    started = perf_counter()

    try:
        image_base64 = _load_test_image_base64()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = int((perf_counter() - started) * 1000)

    # echo 字段用于联调时确认参数是否按预期传到了算法侧。
    return {
        "result_image_base64": image_base64,
        "image_format": "png",
        "width": request.width,
        "height": request.height,
        "elapsed_ms": elapsed_ms,
        "echo": {
            "prompt": request.prompt,
            "model": request.model,
            "watermark_bits": request.watermark_bits,
            "guidance_scale": request.guidance_scale,
        },
    }
