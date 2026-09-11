"""
心理陪伴路由（模块二）

✅ 已实现：
- POST /api/psych/chat  心理陪伴对话（无状态：对话历史由前端传入，不落库）

设计说明：
- 复用 app/ai/llm.py 的 generate_reply（智谱 GLM / DeepSeek 双供应商），
  仅替换系统提示词为「易心」心理陪伴人设（含危机干预护栏）
- 刻意不依赖数据库表，避免演示现场还要额外建表；鉴权仍走统一 get_current_user
- 对话历史超过 N 条时后端截断，控制 token 长度与响应时间
"""
import asyncio
import base64
import hashlib
import json
import re
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai import llm
from app.ai.prompts import build_psych_system_prompt
from app.auth import JWT_SECRET_KEY
from app.database import get_db
from app.models import PsychSession, User
from app.routers.auth import get_current_user
from app.usage import ensure_quota, quota_status, record_usage
from app.voice import verify_assessments, with_voice

router = APIRouter(prefix="/api/psych", tags=["心理陪伴"])

# 单轮最多携带的上下文条数（超出截断最旧部分）
MAX_HISTORY = 30
# 最大用户单条消息长度
MAX_MSG_LEN = 1000

class PsychMessage(BaseModel):
    """单条心理对话消息"""
    role: str = Field(..., description="user / assistant")
    content: str = Field(..., min_length=1, max_length=MAX_MSG_LEN)
    voice_receipts: list[str] = Field(default_factory=list, max_length=8)


class PsychChatRequest(BaseModel):
    """心理对话请求：前端带上完整历史（不含 system）"""
    messages: list[PsychMessage] = Field(..., min_length=1, max_length=MAX_HISTORY)


class PsychChatResponse(BaseModel):
    """心理对话响应"""
    reply: str
    crisis: bool = False  # 本次是否命中危机信号（前端可据此展示热线提示条）
    quota: dict | None = None


class PsychSaveRequest(BaseModel):
    messages: list[PsychMessage] = Field(..., min_length=1, max_length=MAX_HISTORY)
    session_id: int | None = Field(default=None, ge=1)


class PsychFlagsRequest(BaseModel):
    is_favorite: bool | None = None
    is_pinned: bool | None = None


def _to_ms(value: datetime | None) -> int | None:
    return int(value.replace(tzinfo=timezone.utc).timestamp() * 1000) if value else None


def _cipher(user_id: int) -> Fernet:
    raw = hashlib.sha256(f"{JWT_SECRET_KEY}:psych-history:{user_id}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def _encrypt(user_id: int, value: str) -> str:
    return _cipher(user_id).encrypt(value.encode("utf-8")).decode("ascii")


def _decrypt(user_id: int, value: str) -> str:
    try:
        return _cipher(user_id).decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise HTTPException(status_code=500, detail="私密记录解密失败，请联系管理员") from exc


def _summary(messages: list[PsychMessage]) -> str:
    first = next((m.content for m in messages if m.role == "user"), "一次心理陪伴对话")
    cleaned = re.sub(r"\s+", " ", first).strip(" ，。！？")
    return (cleaned[:28] + ("…" if len(cleaned) > 28 else "")) or "一次心理陪伴对话"


def _owned_psych_session(db: Session, session_id: int, user: User) -> PsychSession:
    item = db.query(PsychSession).filter(PsychSession.id == session_id, PsychSession.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="易心历史不存在")
    return item


@router.post("/chat", response_model=PsychChatResponse)
async def psych_chat(
    req: PsychChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """心理陪伴对话：历史消息由前端传回，服务端无状态调用大模型"""
    # 截断历史（保留最近 N 条）
    messages = [
        {"role": m.role if m.role in ("user", "assistant") else "user", "content": with_voice(m.content, verify_assessments(m.voice_receipts, current_user.id, 'psych'))}
        for m in req.messages[-MAX_HISTORY:]
    ]

    system_prompt = build_psych_system_prompt()
    ensure_quota(db, current_user)

    # openai SDK 是同步阻塞调用，放线程池避免卡事件循环
    reply = await asyncio.to_thread(llm.generate_reply, system_prompt, messages)
    reply = (reply or "").strip()
    if not reply:
        reply = "嗯，我在听。你愿意再说说吗？"
    quota = record_usage(db, current_user, system_prompt + json.dumps(messages, ensure_ascii=False), reply)
    return PsychChatResponse(reply=reply, crisis=False, quota=quota)


@router.post("/sessions")
async def save_psych_session(
    req: PsychSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退出前经用户确认后保存；数据库中不落任何心理对话明文。"""
    payload = json.dumps([{**m.model_dump(), 'voice_assessments': verify_assessments(m.voice_receipts, current_user.id, 'psych')} for m in req.messages], ensure_ascii=False)
    item = _owned_psych_session(db, req.session_id, current_user) if req.session_id else None
    if item:
        item.encrypted_summary = _encrypt(current_user.id, _summary(req.messages))
        item.encrypted_payload = _encrypt(current_user.id, payload)
    else:
        item = PsychSession(
            user_id=current_user.id,
            encrypted_summary=_encrypt(current_user.id, _summary(req.messages)),
            encrypted_payload=_encrypt(current_user.id, payload),
        )
        db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "saved": True, "updated": bool(req.session_id), "encrypted": True}


@router.get("/sessions")
async def list_psych_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(PsychSession)
        .filter(PsychSession.user_id == current_user.id)
        .order_by(PsychSession.is_pinned.desc(), PsychSession.updated_at.desc(), PsychSession.id.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": item.id,
            "summary": _decrypt(current_user.id, item.encrypted_summary),
            "is_favorite": bool(item.is_favorite),
            "is_pinned": bool(item.is_pinned),
            "created_at": _to_ms(item.created_at),
            "updated_at": _to_ms(item.updated_at),
            "encrypted": True,
        }
        for item in items
    ]


@router.get("/sessions/{session_id}")
async def get_psych_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _owned_psych_session(db, session_id, current_user)
    return {
        "id": item.id,
        "summary": _decrypt(current_user.id, item.encrypted_summary),
        "messages": json.loads(_decrypt(current_user.id, item.encrypted_payload)),
        "is_favorite": bool(item.is_favorite),
        "is_pinned": bool(item.is_pinned),
        "created_at": _to_ms(item.created_at),
        "encrypted": True,
    }


@router.patch("/sessions/{session_id}")
async def update_psych_session(
    session_id: int,
    req: PsychFlagsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _owned_psych_session(db, session_id, current_user)
    if req.is_favorite is not None:
        item.is_favorite = int(req.is_favorite)
    if req.is_pinned is not None:
        item.is_pinned = int(req.is_pinned)
    db.commit()
    return {"id": item.id, "updated": True}


@router.delete("/sessions/{session_id}")
async def delete_psych_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _owned_psych_session(db, session_id, current_user)
    db.delete(item)
    db.commit()
    return {"id": session_id, "deleted": True}
