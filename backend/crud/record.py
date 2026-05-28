from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.record import WmTaskRecord


async def create_task_record(db: AsyncSession, record_data: dict) -> WmTaskRecord:
    record = WmTaskRecord(**record_data)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_user_records(
    db: AsyncSession,
    user_id: int,
    media_type: str | None = None,
    operation_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[WmTaskRecord], int]:
    query = select(WmTaskRecord).where(WmTaskRecord.user_id == user_id)
    count_query = select(WmTaskRecord).where(WmTaskRecord.user_id == user_id)

    if media_type:
        query = query.where(WmTaskRecord.media_type == media_type)
        count_query = count_query.where(WmTaskRecord.media_type == media_type)
    if operation_type:
        query = query.where(WmTaskRecord.operation_type == operation_type)
        count_query = count_query.where(WmTaskRecord.operation_type == operation_type)

    count_result = await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = query.order_by(WmTaskRecord.id.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_all_records(
    db: AsyncSession,
    media_type: str | None = None,
    operation_type: str | None = None,
    page: int = 1,
    size: int = 20,
    keyword: str | None = None,
    user_id: int | None = None,
) -> tuple[list[WmTaskRecord], int]:
    query = select(WmTaskRecord)
    count_query = select(WmTaskRecord)

    if user_id is not None:
        query = query.where(WmTaskRecord.user_id == user_id)
        count_query = count_query.where(WmTaskRecord.user_id == user_id)
    if media_type:
        query = query.where(WmTaskRecord.media_type == media_type)
        count_query = count_query.where(WmTaskRecord.media_type == media_type)
    if operation_type:
        query = query.where(WmTaskRecord.operation_type == operation_type)
        count_query = count_query.where(WmTaskRecord.operation_type == operation_type)
    if keyword:
        kw = f"%{keyword}%"
        query = query.where(
            WmTaskRecord.username.contains(kw) | WmTaskRecord.watermark_bits.contains(keyword)
        )
        count_query = count_query.where(
            WmTaskRecord.username.contains(kw) | WmTaskRecord.watermark_bits.contains(keyword)
        )

    count_result = await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    query = query.order_by(WmTaskRecord.id.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_record_by_id(db: AsyncSession, record_id: int) -> WmTaskRecord | None:
    result = await db.execute(
        select(WmTaskRecord).where(WmTaskRecord.id == record_id)
    )
    return result.scalar_one_or_none()
