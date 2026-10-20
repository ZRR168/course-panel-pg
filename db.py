"""数据库连接与会话管理（Supabase PostgreSQL）。
所有表结构定义在 models.py，由 seed.py 负责建表 + 种子数据。
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("缺少环境变量 DATABASE_URL（Supabase PostgreSQL 连接串）")

# pool_pre_ping 会自动检测断开的连接；Supabase 事务池端口 6543 适合长驻服务
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, future=True))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.remove()
