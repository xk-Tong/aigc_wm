from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 替换为你的实际 MySQL 数据库连接信息
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:200212@127.0.0.1:3306/aigc_wm"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()