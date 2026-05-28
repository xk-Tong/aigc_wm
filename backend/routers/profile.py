from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import auth as crud_auth
from deps import get_current_user
from schemas.auth import ChangePasswordRequest
from utils.security import get_password_hash, verify_password

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("", response_model=dict)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_obj = await crud_auth.get_user_by_id(db, user["id"])
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "role": user_obj.role,
            "status": user_obj.status,
            "created_at": user_obj.created_at.isoformat() if user_obj.created_at else None,
        },
    }


@router.put("/password", response_model=dict)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    user_obj = await crud_auth.get_user_by_id(db, user["id"])
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(body.old_password, user_obj.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")

    if body.old_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")

    user_obj.password_hash = get_password_hash(body.new_password)
    await db.commit()

    return {
        "code": 200,
        "message": "密码修改成功",
        "data": None,
    }
