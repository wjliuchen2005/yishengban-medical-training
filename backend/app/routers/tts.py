"""Secure backend proxy for Xiaomi MiMo V2.5 TTS."""
import base64
import binascii
import os
import threading
import time
from collections import defaultdict, deque
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.models import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/tts", tags=["语音合成"])
load_dotenv()

Role = Literal["guide", "psych", "patient", "coach", "narrator", "doctor", "registrar", "cashier", "pharmacist"]
Gender = Literal["male", "female", ""]
Voice = Literal["冰糖", "茉莉", "白桦", "苏打"]

_ROLE_STYLE: dict[str, str] = {
    "guide": "亲切明亮的健康伙伴，普通话清晰自然，语速适中，带轻微微笑感。",
    "psych": "温柔、真诚而有陪伴感，语速稍慢，留有自然停顿，不夸张表演。",
    "patient": "像真实患者自然说话，根据文字内容表达相应情绪，避免播音腔。",
    "coach": "沉稳可靠的医学训练教练，表达清楚、有鼓励感，语速稍慢。",
    "narrator": "有画面感但克制的情景旁白，普通话清晰，和医院角色明显区分。",
    "doctor": "专业从容的临床医生，吐字清楚、语气温和而简洁。",
    "registrar": "耐心利落的医院工作人员，表达清晰，语速适中。",
    "cashier": "耐心利落的医院收费人员，表达清晰，语速适中。",
    "pharmacist": "专业耐心的药师，重点明确，药品说明清楚。",
}
_ALLOWED_EMOTIONS = {
    "neutral", "smile", "happy", "calm", "concerned", "anxious", "confused",
    "explaining", "relieved", "listless", "choking", "collapsed", "scared",
}
_EMOTION_STYLE = {
    "happy": "语气开心但克制。", "smile": "带自然微笑感。", "calm": "平静温和。",
    "concerned": "带关切感。", "anxious": "略显着急，但保持吐字清晰。",
    "confused": "带一点疑惑。", "explaining": "像面对面耐心讲解。",
    "relieved": "明显松了一口气。", "listless": "声音较虚弱、缓慢。",
    "choking": "声音急促、艰难，保留可理解度。", "collapsed": "非常虚弱、断续。",
    "scared": "带受惊感和轻微喘息。",
}

_client: OpenAI | None = None
_client_lock = threading.Lock()
_upstream_slots = threading.BoundedSemaphore(value=4)
_requests_by_user: dict[int, deque[float]] = defaultdict(deque)
_rate_lock = threading.Lock()


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    role: Role = "patient"
    gender: Gender = ""
    emotion: str = Field(default="neutral", max_length=24)
    voice: Voice | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            api_key = os.getenv("MIMO_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("MIMO_API_KEY is not configured")
            _client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("MIMO_TTS_BASE_URL", "https://api.xiaomimimo.com/v1"),
                timeout=float(os.getenv("MIMO_TTS_TIMEOUT_SECONDS", "30")),
                max_retries=1,
            )
    return _client


def _voice_for(role: str, gender: str, requested_voice: str | None = None) -> str:
    # 每个场景由声线编排智能体选择医生声线；同场景内其他角色不会复用它。
    if requested_voice in {"冰糖", "茉莉", "白桦", "苏打"}:
        return requested_voice
    if gender == "male":
        return "白桦" if role in {"coach", "doctor", "pharmacist"} else "苏打"
    return "冰糖" if role == "guide" else "茉莉"


def _style_for(role: str, emotion: str) -> str:
    safe_emotion = emotion if emotion in _ALLOWED_EMOTIONS else "neutral"
    return _ROLE_STYLE[role] + _EMOTION_STYLE.get(safe_emotion, "") + "只朗读给出的正文，不增删内容。"


def _check_rate_limit(user_id: int) -> None:
    now = time.monotonic()
    with _rate_lock:
        bucket = _requests_by_user[user_id]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 30:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="语音请求过于频繁，请稍后再试")
        bucket.append(now)


def _synthesize(req: TTSRequest) -> bytes:
    completion = _get_client().chat.completions.create(
        model=os.getenv("MIMO_TTS_MODEL", "mimo-v2.5-tts"),
        messages=[
            {"role": "user", "content": _style_for(req.role, req.emotion)},
            {"role": "assistant", "content": req.text.strip()},
        ],
        audio={"format": "wav", "voice": _voice_for(req.role, req.gender, req.voice)},
    )
    audio = getattr(completion.choices[0].message, "audio", None)
    encoded = getattr(audio, "data", None)
    if not encoded:
        raise RuntimeError("MiMo returned no audio")
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RuntimeError("MiMo returned invalid audio") from exc


@router.post("/synthesize", response_class=Response)
async def synthesize_speech(req: TTSRequest, current_user: User = Depends(get_current_user)) -> Response:
    """Generate role-aware WAV audio while keeping the provider key server-side."""
    if os.getenv("MIMO_TTS_ENABLED", "true").lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="高品质语音暂未启用")
    _check_rate_limit(current_user.id)
    if not _upstream_slots.acquire(blocking=False):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="语音服务繁忙，请稍后重试")
    try:
        audio_bytes = await run_in_threadpool(_synthesize, req)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="高品质语音暂时不可用") from exc
    finally:
        _upstream_slots.release()
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
