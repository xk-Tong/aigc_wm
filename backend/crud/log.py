from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.operation_log import SysOperationLog


async def create_operation_log(db: AsyncSession, log_data: dict) -> SysOperationLog:
    log = SysOperationLog(**log_data)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_operation_logs(
    db: AsyncSession,
    operation: str | None = None,
    page: int = 1,
    size: int = 20,
    user_id: int | None = None,
    keyword: str | None = None,
) -> tuple[list[SysOperationLog], int]:
    query = select(SysOperationLog)
    count_query = select(SysOperationLog)

    if user_id is not None:
        query = query.where(SysOperationLog.user_id == user_id)
        count_query = count_query.where(SysOperationLog.user_id == user_id)
    if operation:
        query = query.where(SysOperationLog.operation == operation)
        count_query = count_query.where(SysOperationLog.operation == operation)
    if keyword:
        kw = f"%{keyword}%"
        query = query.where(SysOperationLog.username.contains(kw))
        count_query = count_query.where(SysOperationLog.username.contains(kw))

    count_result = await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = query.order_by(SysOperationLog.id.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all()), total
