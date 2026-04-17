from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import auth as crud_auth
from schemas.auth import ApiResponse, UserRegister, UserLogin

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    existing_user = await crud_auth.get_user_by_username_or_email(
        db, user_in.username, user_in.email
    )

    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(status_code=400, detail="用户名已被注册")
        if existing_user.email == user_in.email:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    try:
        new_user = await crud_auth.create_user(db, user_in)
    except Exception:
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        },
        "timestamp": crud_auth.get_current_timestamp()
    }


@router.post("/login", response_model=ApiResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.authenticate_user(db, user_in.username, user_in.password)

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user.status == 0:
        raise HTTPException(status_code=403, detail="该账号已被禁用")

    access_token = await crud_auth.generate_access_token(user)
    user_info = crud_auth.get_user_info(user)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "accessToken": access_token,
            "user": user_info.model_dump()
        },
        "timestamp": crud_auth.get_current_timestamp()
    }
