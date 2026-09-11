"""GLM-5.3-Flash 每日保护性额度（按用户给定价格保守估算）。"""
from __future__ import annotations

import math
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import DailyUsage, User

DAILY_LIMIT_RMB = 2.0
INPUT_RMB_PER_MILLION = 0.8
OUTPUT_RMB_PER_MILLION = 2.8
CACHED_INPUT_RMB_PER_MILLION = 0.23
ESTIMATED_COMPLETE_TRAINING_RMB = 0.22


def _today() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def estimate_tokens(text: str) -> int:
    """中文按约1字/token，ASCII按约4字符/token，宁可略高估以保护额度。"""
    text = text or ""
    chinese = len(re.findall(r"[^\x00-\x7F]", text))
    ascii_count = len(text) - chinese
    return max(1, chinese + math.ceil(ascii_count / 4))


def _row(db: Session, user_id: int, create: bool = False) -> DailyUsage | None:
    row = db.query(DailyUsage).filter(DailyUsage.user_id == user_id, DailyUsage.usage_date == _today()).first()
    if row is None and create:
        row = DailyUsage(user_id=user_id, usage_date=_today())
        db.add(row)
        db.flush()
    return row


def quota_status(db: Session, user: User) -> dict:
    row = _row(db, user.id)
    cost = (row.cost_micrormb if row else 0) / 1_000_000
    remaining = max(0.0, DAILY_LIMIT_RMB - cost)
    exhausted = cost >= DAILY_LIMIT_RMB
    return {
        "date": _today(),
        "limit_rmb": DAILY_LIMIT_RMB,
        "used_rmb": round(cost, 4),
        "remaining_rmb": round(remaining, 4),
        "percent": min(100, round(cost / DAILY_LIMIT_RMB * 100)),
        "estimated_training_runs_remaining": max(0, math.floor(remaining / ESTIMATED_COMPLETE_TRAINING_RMB)),
        "exhausted": exhausted,
        "is_test_account": user.username == "test",
        "can_continue": not exhausted or user.username == "test",
        "message": (
            "您的今日额度已用完。此账号为测试账号，额度用完仅是保护性功能展示，可以继续使用。"
            if exhausted and user.username == "test"
            else "您的今日练习额度已用完，请明天再来。"
            if exhausted
            else ""
        ),
    }


def ensure_quota(db: Session, user: User) -> dict:
    info = quota_status(db, user)
    if info["exhausted"] and user.username != "test":
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=info["message"])
    return info


def record_usage(db: Session, user: User, input_text: str, output_text: str, cached_text: str = "") -> dict:
    row = _row(db, user.id, create=True)
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    cached_tokens = estimate_tokens(cached_text) if cached_text else 0
    cost_rmb = (
        input_tokens * INPUT_RMB_PER_MILLION
        + output_tokens * OUTPUT_RMB_PER_MILLION
        + cached_tokens * CACHED_INPUT_RMB_PER_MILLION
    ) / 1_000_000
    row.input_tokens += input_tokens
    row.output_tokens += output_tokens
    row.cached_input_tokens += cached_tokens
    row.cost_micrormb += math.ceil(cost_rmb * 1_000_000)
    db.commit()
    return quota_status(db, user)


def reserve_voice_cost(db: Session, user: User, seconds: float, context: str | None = None) -> dict:
    """Conservative quota reservation, not a provider bill. Reserve before network I/O.

    MiMo 2026-09-09: ASR 0.5 RMB/hour; V2.5 input 1/output 2 RMB/M.
    Assessment reserves max output (1800 tokens); ignores cache discounts.
    """
    row = _row(db, user.id, create=True)
    if context is None:
        cost = seconds / 3600 * float(os.getenv('MIMO_ASR_RMB_PER_HOUR', '0.5'))
    else:
        cost = ((estimate_tokens(context) + math.ceil(seconds * 6.25)) * float(os.getenv('MIMO_AUDIO_INPUT_RMB_PER_MILLION', '1'))
                + 1800 * float(os.getenv('MIMO_AUDIO_OUTPUT_RMB_PER_MILLION', '2'))) / 1_000_000
    # SQL arithmetic avoids lost updates when ASR and assessment run concurrently.
    db.query(DailyUsage).filter(DailyUsage.id == row.id).update({DailyUsage.cost_micrormb: DailyUsage.cost_micrormb + math.ceil(cost * 1_000_000)}, synchronize_session=False)
    db.commit()
    db.expire_all()
    return quota_status(db, user)
