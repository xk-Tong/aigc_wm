from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OperationLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    operation: str
    media_type: Optional[str] = None
    request_path: str
    request_method: str
    ip_address: Optional[str] = None
    status: str
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogListResponse(BaseModel):
    items: list[OperationLogResponse]
    total: int
    page: int
    size: int


class OperationLogQuery(BaseModel):
    operation: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = None
