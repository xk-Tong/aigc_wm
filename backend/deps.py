from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException

from crud import auth as crud_auth
from models.auth import ROLE_HIERARCHY


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """从 Authorization 头提取 token，验证会话，返回 session_data。

    Raises:
        HTTPException(401): token 缺失或会话已失效。
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证信息")

    value = authorization.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()

    if not value:
        raise HTTPException(status_code=401, detail="缺少认证信息")

    session_data = await crud_auth.verify_session_token(value, refresh_ttl=True)
    if not session_data:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")

    return session_data


def require_role(*allowed_roles: str) -> Callable:
    """返回一个 Depends 工厂，检查当前用户角色是否满足层级要求。

    角色层级 SUPER_ADMIN > ADMIN > USER，高等级角色自动通过低等级权限检查。
    不满足时抛 HTTPException(403)。
    """

    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "USER")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        allowed_levels = [ROLE_HIERARCHY.get(r, 0) for r in allowed_roles]
        min_required = min(allowed_levels) if allowed_levels else 0
        if user_level < min_required:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return role_checker
