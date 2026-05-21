from pydantic import BaseModel, Field


class GenerateWatermarkedGSRequest(BaseModel):
    """前端提交"生成含水印 3DGS"时的请求体。"""

    prompt: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="gaussian-splatting")
    # 前端展示 8 位十六进制，这里实际接收的是转换后的 32 位二进制串。
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    seed: int | None = Field(default=None, ge=0)


class GenerateWatermarkedGSResponse(BaseModel):
    """业务后端返回给前端的 3DGS 生成结果。"""

    gs_id: str
    gs_url: str
    download_url: str
    watermark_bits: str
    elapsed_ms: int
    generated_at: str
    model: str
    file_format: str
    gaussian_count: int


class ExtractGSWatermarkResponse(BaseModel):
    """业务后端返回给前端的 3DGS 水印提取结果。"""

    file_id: str
    file_name: str
    watermark_bits: str
    elapsed_ms: int
    extracted_at: str
    file_size_bytes: int
