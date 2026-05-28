from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.auth import Base


class SysOperationLog(Base):
    """系统操作日志表 — 审计追踪"""

    __tablename__ = "sys_operation_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)  # login | logout | register | embed | extract | user_manage | ...
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    request_path: Mapped[str] = mapped_column(String(256), nullable=False)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # success | fail
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
