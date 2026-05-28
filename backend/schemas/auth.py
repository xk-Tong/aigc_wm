from pydantic import BaseModel, EmailStr, Field
from typing import Any, Optional
from datetime import datetime

class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any = Field(default_factory=dict)
    timestamp: str

class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="电子邮箱")
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True

class UserManagementItem(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)

class UpdateRoleRequest(BaseModel):
    role: str = Field(pattern="^(USER|ADMIN|SUPER_ADMIN)$")

class UpdateStatusRequest(BaseModel):
    status: int = Field(ge=0, le=1)