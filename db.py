"""数据库连接与会话管理（Supabase PostgreSQL）。

策略：
1. 若设置了 DATABASE_URL 且能连上，直接用；
2. 否则根据 SUPABASE_URL 里的项目 ref 自动探测正确的连接池地址
   （并发尝试所有区域/集群 + 直连，连上哪个用哪个）；
3. 数据库密码取 DB_PASSWORD，缺省为 ausrealt168。
"""
import os
import re
import socket
import concurrent.futures
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL_OVERRIDE = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or "ausrealt168"

# 从 Supabase URL 中提取项目 ref（形如 https://<ref>.supabase.co）
REF = None
m = re.search(r"https?://([a-z0-9]+)\.supabase\.co", SUPABASE_URL)
if m:
    REF = m.group(1)


def _candidates():
    cands = []
    if DATABASE_URL_OVERRIDE:
        cands.append(("explicit", DATABASE_URL_OVERRIDE))
    if REF:
        regions = [
            "ap-southeast-2", "ap-southeast-1", "ap-northeast-1", "ap-northeast-2",
            "ap-south-1", "ap-east-1", "us-east-1", "us-east-2", "us-west-1",
            "us-west-2", "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
            "eu-north-1", "ca-central-1", "sa-east-1",
        ]
        prefixes = ["aws-0-", "aws-1-"]
        for r in regions:
            for pfx in prefixes:
                host = f"{pfx}{r}.pooler.supabase.com"
                cands.append((host,
                    f"postgresql://postgres.{REF}:{DB_PASSWORD}@{host}:6543/postgres?sslmode=require"))
            # 直连 / 会话池（不用事务池前缀）
            cands.append((f"db.{REF}.supabase.co",
                f"postgresql://postgres.{REF}:{DB_PASSWORD}@db.{REF}.supabase.co:5432/postgres?sslmode=require"))
            cands.append((f"{r}.pooler.supabase.com",
                f"postgresql://postgres.{REF}:{DB_PASSWORD}@{r}.pooler.supabase.com:6543/postgres?sslmode=require"))
    return cands


def _try_connect(label, url):
    try:
        from sqlalchemy import create_engine as _ce
        eng = _ce(url, pool_pre_ping=True, connect_args={"connect_timeout": 4}, future=True)
        conn = eng.connect()
        conn.close()
        eng.dispose()
        return url
    except Exception:
        return None


def _discover():
    cands = _candidates()
    if not cands:
        return None
    # 并发试连，先连上者胜出（整体耗时受单个 connect_timeout 限制）
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_try_connect, l, u): (l, u) for l, u in cands}
        for fut in concurrent.futures.as_completed(futs):
            res = fut.result()
            if res:
                return res
    return None


_DATABASE_URL = None
try:
    _DATABASE_URL = _discover()
except Exception:
    _DATABASE_URL = None

if not _DATABASE_URL:
    # 兜底：哪怕连不上也先建好 engine（首次查询时才真正连），避免导入即崩溃
    if DATABASE_URL_OVERRIDE:
        _DATABASE_URL = DATABASE_URL_OVERRIDE
    elif REF:
        _DATABASE_URL = f"postgresql://postgres.{REF}:{DB_PASSWORD}@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
    else:
        _DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"

engine = create_engine(
    _DATABASE_URL,
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
