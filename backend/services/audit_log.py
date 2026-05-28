import json

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from models.operation_log import SysOperationLog


async def log_operation(
    db: AsyncSession,
    user: dict | None,
    operation: str,
    media_type: str | None,
    request: Request,
    status: str,
    detail: dict | None = None,
) -> SysOperationLog:
    log = SysOperationLog(
        user_id=user["id"] if user else None,
        username=user["username"] if user else None,
        operation=operation,
        media_type=media_type,
        request_path=str(request.url.path),
        request_method=request.method,
        ip_address=request.client.host if request.client else None,
        status=status,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
