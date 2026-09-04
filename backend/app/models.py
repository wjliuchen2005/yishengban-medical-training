"""
SQLAlchemy ORM 模型

对应 database/init.sql 中的表结构。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50))
    student_id = Column(String(20), index=True)
    school = Column(String(100), default="南京医科大学")
    email = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Scene(Base):
    """场景表"""
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cover = Column(String(255))
    role = Column(String(50))  # 角色信息
    role_avatar = Column(String(255))
    background = Column(Text)
    opening_message = Column(Text)
    config = Column(JSON)  # 场景配置 JSON
    difficulty = Column(Integer, default=1)  # 1-5
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    scene_id = Column(Integer, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    is_rated = Column(Integer, default=0)


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, index=True, nullable=False)
    role = Column(String(20), nullable=False)  # system/user/ai/coach
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON)  # 额外信息（如评分标注、教练提示）


class Result(Base):
    """评分结果表"""
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    total_score = Column(Integer)
    accuracy = Column(Integer)
    warmth = Column(Integer)
    decision = Column(Integer)
    details = Column(JSON)  # 详细评分 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
