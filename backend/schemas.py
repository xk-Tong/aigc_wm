from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str  # 前端支持邮箱或用户名登录
    password: str

class Token(BaseModel):
    accessToken: str
    token_type: str