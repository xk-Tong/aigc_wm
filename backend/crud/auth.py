from datetime import datetime, timezone
import json
from typing import Optional

from sqlalchemy import func, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache_conf import redis_client
from models import auth
from schemas.auth import UserRegister, UserInfo
from utils.security import (
    SESSION_TOKEN_TTL_SECONDS,
    create_session_token,
    get_password_hash,
    verify_password,
)


def _build_session_key(token: str) -> str:
    return f"session:{token}"


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


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[auth.User]:
    result = await db.execute(select(auth.User).where(auth.User.id == user_id))
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
        str: UUID 会话令牌
    """
    token = create_session_token()
    session_key = f"session:{token}"
    session_payload = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "status": user.status,
    }

    try:
        # 登录成功后将会话信息写入 Redis，并设置统一会话过期时间。
        await redis_client.setex(
            session_key,
            SESSION_TOKEN_TTL_SECONDS,
            json.dumps(session_payload, ensure_ascii=False),
        )
    except Exception as exc:
        raise RuntimeError("会话写入缓存失败") from exc

    return token


async def verify_session_token(token: str, refresh_ttl: bool = True) -> Optional[dict]:
    """
    校验 Redis 会话 token，并按需刷新过期时间。

    Args:
        token: 客户端传入的会话 token
        refresh_ttl: 是否在校验成功后刷新 TTL

    Returns:
        Optional[dict]: 校验成功返回会话数据，失败返回 None
    """
    if not token:
        return None

    session_key = _build_session_key(token)

    try:
        session_raw = await redis_client.get(session_key)
        if not session_raw:
            return None

        session_data = json.loads(session_raw)
        if refresh_ttl:
            await redis_client.expire(session_key, SESSION_TOKEN_TTL_SECONDS)
        return session_data
    except Exception:
        return None


async def delete_session_token(token: str) -> bool:
    """
    删除 Redis 中的会话 token。

    Args:
        token: 客户端传入的会话 token

    Returns:
        bool: 删除成功或 token 已不存在时返回 False/True 由调用方决定
    """
    if not token:
        return False

    session_key = _build_session_key(token)

    try:
        deleted_count = await redis_client.delete(session_key)
        return deleted_count > 0
    except Exception:
        return False


def get_user_info(user: auth.User) -> UserInfo:
    """
    获取用户信息
    
    Args:
        user: 用户对象
        
    Returns:
        UserInfo: 用户信息对象
    """
    return UserInfo.model_validate(user)


async def update_user_role(db: AsyncSession, user_id: int, new_role: str) -> auth.User | None:
    """修改用户角色"""
    result = await db.execute(select(auth.User).where(auth.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_status(db: AsyncSession, user_id: int, status: int) -> auth.User | None:
    """启用/禁用用户 (status: 1=正常, 0=禁用)"""
    result = await db.execute(select(auth.User).where(auth.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.status = status
    await db.commit()
    await db.refresh(user)
    return user


async def reset_user_password(db: AsyncSession, user_id: int, new_password: str) -> auth.User | None:
    """重置用户密码"""
    result = await db.execute(select(auth.User).where(auth.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    keyword: str | None = None,
    role_filter: str | None = None,
    status_filter: int | None = None,
) -> tuple[list[auth.User], int]:
    """分页查询用户列表"""
    query = select(auth.User)
    count_query = select(auth.User)

    # 关键字搜索（用户名或邮箱）
    if keyword:
        keyword_filter = or_(auth.User.username.contains(keyword), auth.User.email.contains(keyword))
        query = query.where(keyword_filter)
        count_query = count_query.where(keyword_filter)

    # 角色筛选
    if role_filter:
        query = query.where(auth.User.role == role_filter)
        count_query = count_query.where(auth.User.role == role_filter)

    # 状态筛选
    if status_filter is not None:
        query = query.where(auth.User.status == status_filter)
        count_query = count_query.where(auth.User.status == status_filter)

    # 统计总数
    count_result = await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )
    total = count_result.scalar() or 0

    # 分页
    offset = (page - 1) * size
    query = query.order_by(auth.User.id.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    return list(users), total


def get_current_timestamp() -> str:
    """
    获取当前UTC时间戳

    Returns:
        str: 格式化的时间戳字符串
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
