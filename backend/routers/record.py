from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import record as crud_record
from deps import get_current_user
from models.auth import ROLE_HIERARCHY
from schemas.record import TaskRecordListResponse, TaskRecordResponse

router = APIRouter(prefix="/api/v1/records", tags=["records"])


@router.get("", response_model=dict)
async def list_records(
    media_type: str | None = Query(default=None),
    operation_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_role = user.get("role", "USER")
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    if user_level >= ROLE_HIERARCHY["ADMIN"]:
        # 管理员可查看所有记录，可选按 user_id 筛选
        items, total = await crud_record.get_all_records(
            db, media_type=media_type, operation_type=operation_type,
            page=page, size=size, keyword=keyword, user_id=user_id,
        )
    else:
        # 普通用户只能查看自己的记录
        items, total = await crud_record.get_user_records(
            db, user_id=user["id"], media_type=media_type,
            operation_type=operation_type, page=page, size=size,
        )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [TaskRecordResponse.model_validate(r).model_dump() for r in items],
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.get("/{record_id}", response_model=dict)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    record = await crud_record.get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    user_role = user.get("role", "USER")
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    if user_level < ROLE_HIERARCHY["ADMIN"] and record.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="无权访问该记录")

    return {
        "code": 200,
        "message": "success",
        "data": TaskRecordResponse.model_validate(record).model_dump(),
    }
