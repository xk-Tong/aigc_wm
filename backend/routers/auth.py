from fastapi import APIRouter, Depends, HTTPException, status
from models import auth
from schemas.auth import ResponseModel, UserRegister, UserLogin, UserInfo
from utils.security import get_password_hash, verify_password, create_access_token
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def success_response(message: str, data=None):
    return ResponseModel(code=200, message=message, data=data)

@router.post("/register", response_model=ResponseModel)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(auth.User).where(or_(auth.User.username == user_in.username, auth.User.email == user_in.email))
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(status_code=400, detail="用户名已被注册")
        if existing_user.email == user_in.email:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    new_user = auth.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role="USER",
        status=1
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")
    
    return success_response("注册成功")

@router.post("/login", response_model=ResponseModel)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(auth.User).where(or_(auth.User.username == user_in.username, auth.User.email == user_in.username))
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    if user.status == 0:
        raise HTTPException(status_code=403, detail="该账号已被禁用")

    access_token = create_access_token(data={"sub": user.username, "id": user.id})
    
    return success_response("登录成功", data={
        "accessToken": access_token,
        "user": UserInfo.model_validate(user).model_dump()
    })

