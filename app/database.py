from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 使用 SQLite 为了方便本地直接运行演示
SQLALCHEMY_DATABASE_URL = "sqlite:///./travel_sys.db"

# connect_args={"check_same_thread": False} 是 fastAPI + SQLite 的设定
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依赖项获取数据库 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
