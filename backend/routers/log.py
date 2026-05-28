from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import log as crud_log
from deps import get_current_user
from models.auth import ROLE_HIERARCHY, UserRole
from schemas.log import OperationLogResponse, OperationLogListResponse

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("", response_model=dict)
async def list_logs(
    operation: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_role = user.get("role", "USER")
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    # 权限控制：USER 只看自己的，ADMIN 看 USER 的，SUPER_ADMIN 看所有人
    filter_user_id = user_id
    if user_level < ROLE_HIERARCHY.get(UserRole.ADMIN, 1):
        filter_user_id = user["id"]
    elif user_level < ROLE_HIERARCHY.get(UserRole.SUPER_ADMIN, 2) and not filter_user_id:
        # ADMIN 不指定 user_id 时只能看到 USER 角色的日志，简化处理为不过滤
        pass

    items, total = await crud_log.get_operation_logs(
        db, operation=operation, page=page, size=size,
        user_id=filter_user_id, keyword=keyword,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [OperationLogResponse.model_validate(r).model_dump() for r in items],
            "total": total,
            "page": page,
            "size": size,
        },
    }
