from pydantic import BaseModel, Field


class GenerateWatermarkedMeshRequest(BaseModel):
    """前端提交"生成含水印网格模型"时的请求体。"""

    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="trellis")
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    seed: int | None = Field(default=None, ge=0)


class GenerateWatermarkedMeshResponse(BaseModel):
    """业务后端返回给前端的网格模型生成结果。"""

    mesh_id: str
    mesh_url: str
    download_url: str
    watermark_bits: str
    elapsed_ms: int
    generated_at: str
    model: str
    file_format: str


class ExtractMeshWatermarkResponse(BaseModel):
    """业务后端返回给前端的网格水印提取结果。"""

    file_id: str
    file_name: str
    watermark_bits: str
    elapsed_ms: int
    extracted_at: str
    file_size_bytes: int
