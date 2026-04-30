from pydantic import BaseModel, Field


class GenerateWatermarkedImageRequest(BaseModel):
    """前端提交“生成含水印图像”时的请求体。"""

    # 提示词：描述想生成的画面内容。
    prompt: str = Field(..., min_length=1, max_length=2000)
    # 模型名称：用于告诉算法侧选哪个模型。
    model: str = Field(default="flux2")
    # 32 位二进制水印内容，例如 0101...
    watermark_bits: str = Field(..., pattern=r"^[01]{32}$")
    # 输出分辨率（宽高）。
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    # 生成引导系数：用于控制提示词对结果的影响程度。
    guidance_scale: float = Field(default=1.0, ge=0.0, le=20.0)


class GenerateWatermarkedImageResponse(BaseModel):
    """业务后端返回给前端的图像生成结果。"""

    # 图片唯一 ID，可用于后续追踪或扩展任务系统。
    image_id: str
    # 前端展示用 URL。
    image_url: str
    # 前端下载用 URL（当前与 image_url 一致，后续可分离）。
    download_url: str
    # 回显实际嵌入的水印内容。
    watermark_bits: str
    # 处理耗时（毫秒）。
    elapsed_ms: int
    # 生成时间（UTC 字符串）。
    generated_at: str
    model: str
    width: int
    height: int


class ExtractWatermarkResponse(BaseModel):
    """业务后端返回给前端的图像水印提取结果。"""

    # 上传文件在本次请求中的唯一标识。
    file_id: str
    # 原始文件名，方便用户确认当前处理的是哪张图。
    file_name: str
    # 提取出的 32 位二进制水印。
    watermark_bits: str
    # 处理耗时（毫秒）。
    elapsed_ms: int
    # 提取时间（UTC 字符串）。
    extracted_at: str
    # 保存后的文件大小，便于排查与记录。
    file_size_bytes: int
