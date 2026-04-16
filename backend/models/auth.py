from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase,mapped_column, Mapped
from datetime import datetime


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# class User(Base):
#     __tablename__ = "sys_user"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(64), unique=True, index=True, nullable=False)
#     password_hash = Column(String(256), nullable=False)
#     email = Column(String(128), unique=True, index=True)
#     role = Column(String(20), default="USER")
#     status = Column(Integer, default=1) # 0=禁用 1=正常
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="USER")
    status: Mapped[int] = mapped_column(Integer, default=1) # 0=禁用 1=正常