import bcrypt
from jose import jwt
from datetime import datetime, timedelta

# JWT 配置
SECRET_KEY = "your-super-secret-key-please-change-it" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24小时

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    # bcrypt 要求输入必须是 bytes 类型
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except ValueError:
        # 如果哈希值格式不对等导致 ValueError，直接返回验证失败
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # bcrypt 限制最大长度为 72 bytes，对超长密码进行截断（避免抛出异常）
    password_bytes = password.encode('utf-8')[:72]
    
    # 生成盐并计算哈希
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    
    # 将 bytes 解码回字符串，方便存入数据库
    return hashed_password.decode('utf-8')

def create_access_token(data: dict):
    """生成 JWT 令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt