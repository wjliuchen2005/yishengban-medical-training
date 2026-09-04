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
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai import llm
from app.ai.prompts import build_psych_system_prompt
from app.models import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/psych", tags=["心理陪伴"])

# 单轮最多携带的上下文条数（超出截断最旧部分）
MAX_HISTORY = 30
# 最大用户单条消息长度
MAX_MSG_LEN = 1000

# 危机关键词：命中即不依赖大模型，直接走转介话术（保障安全底线）
CRISIS_PATTERNS = re.compile(
    r"自杀|自残|不想活|活着没意思|不想活了|结束生命|离开这个世界|"
    r"割腕|跳楼|安眠药.*(吞|吃|死)|伤害自己|没有出路|撑不下去|遗书",
    re.IGNORECASE,
)

# 危机转介话术（温柔 + 明确求助路径，开头带（worry）让数字人呈担心神态）
CRISIS_REPLY_TEMPLATE = (
    "（worry）\n"
    "谢谢你愿意把这么重的话告诉我，我在很认真地听，也很在乎你说的每一句。"
    "现在这样的时刻，你不需要一个人扛——请你先别一个人待着。"
    "请立刻拨打全国心理援助热线 **12356**（24 小时，免费，会有专业人员陪着你）；"
    "如果你已经在自己伤害自己、或正处于危险中，请马上拨打 110/120。"
    "这不是你的错，你值得被好好接住。我会一直在这里，等你愿意继续说话。"
)


class PsychMessage(BaseModel):
    """单条心理对话消息"""
    role: str = Field(..., description="user / assistant")
    content: str = Field(..., min_length=1, max_length=MAX_MSG_LEN)


class PsychChatRequest(BaseModel):
    """心理对话请求：前端带上完整历史（不含 system）"""
    messages: list[PsychMessage] = Field(..., min_length=1, max_length=MAX_HISTORY)


class PsychChatResponse(BaseModel):
    """心理对话响应"""
    reply: str
    crisis: bool = False  # 本次是否命中危机信号（前端可据此展示热线提示条）


@router.post("/chat", response_model=PsychChatResponse)
async def psych_chat(req: PsychChatRequest, current_user: User = Depends(get_current_user)):
    """心理陪伴对话：历史消息由前端传回，服务端无状态调用大模型"""
    # 危机兜底：命中关键词直接返回转介话术（即使大模型走偏也能兜住）
    latest = req.messages[-1] if req.messages else None
    if latest and latest.role == "user" and CRISIS_PATTERNS.search(latest.content):
        return PsychChatResponse(reply=CRISIS_REPLY_TEMPLATE, crisis=True)

    # 截断历史（保留最近 N 条）
    messages = [
        {"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content}
        for m in req.messages[-MAX_HISTORY:]
    ]

    system_prompt = build_psych_system_prompt()

    # openai SDK 是同步阻塞调用，放线程池避免卡事件循环
    reply = await asyncio.to_thread(llm.generate_reply, system_prompt, messages)
    reply = (reply or "").strip()
    if not reply:
        reply = "嗯，我在听。你愿意再说说吗？"
    return PsychChatResponse(reply=reply, crisis=False)
