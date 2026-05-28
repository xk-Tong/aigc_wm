from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import auth as crud_auth
from deps import get_current_user
from models.auth import ROLE_HIERARCHY, UserRole
from schemas.auth import (
    ResetPasswordRequest,
    UpdateRoleRequest,
    UpdateStatusRequest,
    UserManagementItem,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=dict)
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_role = user.get("role", "USER")
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    if user_level < ROLE_HIERARCHY.get(UserRole.ADMIN, 1):
        raise HTTPException(status_code=403, detail="权限不足")

    # ADMIN 只能看到 USER 角色用户
    role_filter = role
    if user_level < ROLE_HIERARCHY.get(UserRole.SUPER_ADMIN, 2):
        if role_filter and role_filter != UserRole.USER:
            raise HTTPException(status_code=403, detail="无权查看该角色的用户")
        role_filter = role_filter or UserRole.USER

    users, total = await crud_auth.list_users(
        db, page=page, size=size, keyword=keyword,
        role_filter=role_filter, status_filter=status,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [UserManagementItem.model_validate(u).model_dump() for u in users],
            "total": total,
            "page": page,
            "size": size,
        },
    }


def _check_user_management_permission(current_user: dict, target_user_role: str, action: str) -> None:
    """校验用户管理权限。ADMIN 只能管理 USER；SUPER_ADMIN 可管理所有人。"""
    current_role = current_user.get("role", "USER")
    current_level = ROLE_HIERARCHY.get(current_role, 0)
    target_level = ROLE_HIERARCHY.get(target_user_role, 0)

    if current_level < ROLE_HIERARCHY.get(UserRole.ADMIN, 1):
        raise HTTPException(status_code=403, detail="权限不足")

    if current_level < ROLE_HIERARCHY.get(UserRole.SUPER_ADMIN, 2) and target_level > 0:
        raise HTTPException(status_code=403, detail=f"无权{action}管理员或超级管理员")


@router.put("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: int,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    target = await crud_auth.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    _check_user_management_permission(user, target.role, "修改")

    updated = await crud_auth.update_user_status(db, user_id, body.status)
    return {
        "code": 200,
        "message": "success",
        "data": UserManagementItem.model_validate(updated).model_dump(),
    }


@router.put("/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    body: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    target = await crud_auth.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    _check_user_management_permission(user, target.role, "修改角色")

    current_role = user.get("role", "USER")
    current_level = ROLE_HIERARCHY.get(current_role, 0)
    new_role_level = ROLE_HIERARCHY.get(body.role, 0)

    # ADMIN 不能将用户升级到高于自己的角色
    if current_level < ROLE_HIERARCHY.get(UserRole.SUPER_ADMIN, 2):
        if new_role_level > ROLE_HIERARCHY.get(UserRole.ADMIN, 1):
            raise HTTPException(status_code=403, detail="无权设置该角色")
        if body.role not in (UserRole.USER, UserRole.ADMIN):
            raise HTTPException(status_code=403, detail="无权设置该角色")

    updated = await crud_auth.update_user_role(db, user_id, body.role)
    return {
        "code": 200,
        "message": "success",
        "data": UserManagementItem.model_validate(updated).model_dump(),
    }


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    target = await crud_auth.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    _check_user_management_permission(user, target.role, "重置密码")

    updated = await crud_auth.reset_user_password(db, user_id, body.new_password)
    return {
        "code": 200,
        "message": "密码重置成功",
        "data": None,
    }
