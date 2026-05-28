from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import auth as crud_auth
from schemas.auth import ApiResponse, UserRegister, UserLogin
from services.audit_log import log_operation

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    value = authorization.strip()
    if not value:
        return None

    if value.lower().startswith("bearer "):
        value = value[7:].strip()

    return value or None


@router.post("/register", response_model=ApiResponse)
async def register(user_in: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
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
    except IntegrityError:
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")

    await log_operation(db, {"id": new_user.id, "username": new_user.username}, "register", None, request, "success")

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
async def login(user_in: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    user = await crud_auth.authenticate_user(db, user_in.username, user_in.password)

    if not user:
        await log_operation(db, None, "login", None, request, "fail", {"username": user_in.username})
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user.status == 0:
        await log_operation(db, {"id": user.id, "username": user.username}, "login", None, request, "fail", {"reason": "account_disabled"})
        raise HTTPException(status_code=403, detail="该账号已被禁用")

    try:
        access_token = await crud_auth.generate_access_token(user)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="登录服务暂不可用，请稍后再试")

    user_info = crud_auth.get_user_info(user)
    await log_operation(db, {"id": user.id, "username": user.username}, "login", None, request, "success")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "accessToken": access_token,
            "user": user_info.model_dump()
        },
        "timestamp": crud_auth.get_current_timestamp()
    }


@router.post("/verify-token", response_model=ApiResponse)
async def verify_token(authorization: Optional[str] = Header(default=None)):
    token = _extract_token(authorization)
    if not token:
        return {
            "code": 200,
            "message": "success",
            "data": {"valid": False},
            "timestamp": crud_auth.get_current_timestamp(),
        }

    session_data = await crud_auth.verify_session_token(token, refresh_ttl=True)
    if not session_data:
        return {
            "code": 200,
            "message": "success",
            "data": {"valid": False},
            "timestamp": crud_auth.get_current_timestamp(),
        }

    return {
        "code": 200,
        "message": "success",
        "data": {
            "valid": True,
            "user": session_data,
        },
        "timestamp": crud_auth.get_current_timestamp(),
    }


@router.post("/logout", response_model=ApiResponse)
async def logout(authorization: Optional[str] = Header(default=None), request: Request = None, db: AsyncSession = Depends(get_db)):
    token = _extract_token(authorization)

    session_data = None
    if token:
        session_data = await crud_auth.verify_session_token(token, refresh_ttl=False)

    deleted = False
    if token:
        deleted = await crud_auth.delete_session_token(token)

    if session_data:
        await log_operation(db, session_data, "logout", None, request, "success")

    return {
        "code": 200,
        "message": "success",
        "data": {"success": True, "revoked": deleted},
        "timestamp": crud_auth.get_current_timestamp(),
    }
