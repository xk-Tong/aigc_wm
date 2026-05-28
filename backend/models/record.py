from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.auth import Base


class WmTaskRecord(Base):
    """水印任务记录表 — 存储所有嵌入/提取操作的业务数据"""

    __tablename__ = "wm_task_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # image | pointcloud | mesh | gs
    operation_type: Mapped[str] = mapped_column(String(10), nullable=False)  # embed | extract

    # 嵌入操作专用字段
    watermark_bits: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    watermarked_file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # 提取操作专用字段
    source_file_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_bits: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 公共字段
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="success")  # success | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str] = mapped_column(String(64), nullable=False)
