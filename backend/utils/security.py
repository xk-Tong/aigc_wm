import os
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-please-change-it-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     password_bytes = plain_password.encode('utf-8')
#     hashed_password_bytes = hashed_password.encode('utf-8')
#     try:
#         return bcrypt.checkpw(password_bytes, hashed_password_bytes)
#     except (ValueError, AttributeError):
#         return False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError, UnknownHashError):
        return False

# def get_password_hash(password: str) -> str:
#     if len(password) < 8:
#         raise ValueError("密码长度至少8位")
#     password_bytes = password.encode('utf-8')[:72]
#     salt = bcrypt.gensalt()
#     return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def get_password_hash(password: str) -> str:
    if len(password) < 8:
        raise ValueError("密码长度至少8位")
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None