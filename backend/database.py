"""数据库连接与初始化。

首期原型默认使用 SQLite，便于本地零配置直接运行。
后续若要切换到 MySQL（立项书指定），只需修改 DATABASE_URL，例如：
    DATABASE_URL="mysql+pymysql://user:password@localhost/zhiji?charset=utf8mb4"
并额外安装驱动：pip install pymysql
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zhiji.db")

# SQLite 需要关闭多线程校验；MySQL 等无需该参数
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：为每个请求提供一个数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
