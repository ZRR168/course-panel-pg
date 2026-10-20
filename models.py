"""SQLAlchemy 模型：users / sessions / claim_history / activity_log。
对应 PDF 第25-27页「助教分配总表」的课程结构。
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, ARRAY,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# 6 大模块（code -> 名称），与 PDF 一致
MODULES = {
    "M1": "思维入口",
    "M2": "技能库",
    "M3": "项目实战",
    "M4": "商业化",
    "M5": "工作流",
    "M6": "财富+毕业",
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    role = Column(String(20), default="ta", nullable=False)  # admin | ta
    password_hash = Column(String(255), nullable=False)
    claim_scope = Column(ARRAY(String), default=list)  # 可认领模块 code；空=全部
    active = Column(Boolean, default=True)
    must_change_pw = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    claims = relationship("CourseSession", back_populates="claimer")


class CourseSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    week = Column(Integer, nullable=False)
    module = Column(String(10), nullable=False)        # M1..M6
    topic = Column(String(200), nullable=False)
    slot = Column(String(10), nullable=False)          # 1-A / 1-B / 1-C / 2-A / 2-B
    class_time = Column(DateTime, nullable=True)
    claimed_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="open", nullable=False)  # open | claimed | locked
    note = Column(Text, default="")
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    claimer = relationship("User", back_populates="claims")


class ClaimHistory(Base):
    __tablename__ = "claim_history"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(20), nullable=False)  # claim | release | assign
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
