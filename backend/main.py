from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import engine, Base, get_db
from models import User
from schemas import UserRegister, UserLogin
from security import get_password_hash, verify_password, create_access_token

# 如果你的表还没建好，可以取消下面这行的注释自动建表
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIGC Watermark API")

# 配置 CORS，允许前端联调跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境下允许所有，生产环境建议指定前端域名 (如 http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/auth/register")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 检查用户名或邮箱是否已存在
    db_user = db.query(User).filter(
        or_(User.username == user_in.username, User.email == user_in.email)
    ).first()
    
    if db_user:
        if db_user.username == user_in.username:
            raise HTTPException(status_code=400, detail="用户名已被注册")
        if db_user.email == user_in.email:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建新用户
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role="USER",
        status=1
    )
    db.add(new_user)
    db.commit()
    
    return {"code": 200, "message": "注册成功"}

@app.post("/api/v1/auth/login")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # 支持用户名或邮箱登录
    user = db.query(User).filter(
        or_(User.username == user_in.username, User.email == user_in.username)
    ).first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        return {"code": 401, "message": "用户名或密码错误"}
        
    if user.status == 0:
        return {"code": 403, "message": "该账号已被禁用"}

    # 生成 Token
    access_token = create_access_token(data={"sub": user.username, "id": user.id})
    
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "accessToken": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)