from pydantic import BaseModel, Field


class GenerateWatermarkedPointcloudRequest(BaseModel):
    """前端提交"生成含水印点云"时的请求体。"""

    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="trellis")
    watermark_bits: str = Field(..., pattern=r"^[0-9A-Fa-f]{8}$")
    seed: int | None = Field(default=None, ge=0)


class GenerateWatermarkedPointcloudResponse(BaseModel):
    """业务后端返回给前端的点云生成结果。"""

    pointcloud_id: str
    pointcloud_url: str
    download_url: str
    watermark_bits: str
    elapsed_ms: int
    generated_at: str
    model: str
    file_format: str


class ExtractPointcloudWatermarkResponse(BaseModel):
    """业务后端返回给前端的点云水印提取结果。"""

    file_id: str
    file_name: str
    watermark_bits: str
    elapsed_ms: int
    extracted_at: str
    file_size_bytes: int
