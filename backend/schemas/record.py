from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskRecordResponse(BaseModel):
    id: int
    user_id: int
    username: str
    media_type: str
    operation_type: str
    watermark_bits: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    original_file_url: Optional[str] = None
    watermarked_file_url: Optional[str] = None
    download_url: Optional[str] = None
    source_file_name: Optional[str] = None
    source_file_size: Optional[int] = None
    extracted_bits: Optional[str] = None
    elapsed_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    file_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskRecordListResponse(BaseModel):
    items: list[TaskRecordResponse]
    total: int
    page: int
    size: int


class TaskRecordQuery(BaseModel):
    media_type: Optional[str] = None
    operation_type: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = None
