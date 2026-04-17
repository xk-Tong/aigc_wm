from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import auth
from schemas.auth import UserRegister, UserInfo
from utils.security import get_password_hash, verify_password, create_access_token


async def get_user_by_username_or_email(db: AsyncSession, username: str, email: str) -> Optional[auth.User]:
    """
    根据用户名或邮箱查询用户
    
    Args:
        db: 数据库会话
        username: 用户名
        email: 邮箱地址
        
    Returns:
        Optional[auth.User]: 用户对象，如果不存在则返回None
    """
    result = await db.execute(
        select(auth.User).where(
            or_(auth.User.username == username, auth.User.email == email)
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[auth.User]:
    """
    根据用户名查询用户
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        Optional[auth.User]: 用户对象，如果不存在则返回None
    """
    result = await db.execute(
        select(auth.User).where(
            or_(auth.User.username == username, auth.User.email == username)
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserRegister) -> auth.User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        user_in: 用户注册信息
        
    Returns:
        auth.User: 创建的用户对象
        
    Raises:
        IntegrityError: 当用户名或邮箱已存在时
    """
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
        raise
    return new_user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[auth.User]:
    """
    验证用户登录信息
    
    Args:
        db: 数据库会话
        username: 用户名或邮箱
        password: 密码
        
    Returns:
        Optional[auth.User]: 验证成功返回用户对象，失败返回None
    """
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def generate_access_token(user: auth.User) -> str:
    """
    生成用户访问令牌
    
    Args:
        user: 用户对象
        
    Returns:
        str: JWT访问令牌
    """
    return create_access_token(data={"sub": user.username, "id": user.id})


def get_user_info(user: auth.User) -> UserInfo:
    """
    获取用户信息
    
    Args:
        user: 用户对象
        
    Returns:
        UserInfo: 用户信息对象
    """
    return UserInfo.model_validate(user)


def get_current_timestamp() -> str:
    """
    获取当前UTC时间戳
    
    Returns:
        str: 格式化的时间戳字符串
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
