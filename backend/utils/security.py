import os
from uuid import uuid4

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

SESSION_TOKEN_TTL_SECONDS = int(os.getenv("SESSION_TOKEN_TTL_SECONDS", 24 * 60 * 60))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError, UnknownHashError):
        return False

def get_password_hash(password: str) -> str:
    if len(password) < 8:
        raise ValueError("密码长度至少8位")
    return pwd_context.hash(password)

def create_session_token() -> str:
    # uuid4().hex 返回 32 位随机字符串，适合作为会话 token。
    return uuid4().hex