"""
对话相关路由

✅ 已实现：
- POST /api/chat/start 开始一个新对话会话
- POST /api/chat/message 发送消息并获取 AI 回复（患者智能体 + 教练智能体）
- GET  /api/chat/session/{id} 获取会话详情
- POST /api/chat/coach 向观察者教练提问（问答不混入角色扮演历史）
- GET  /api/chat/session/{id}/pressure 时间压力轮询（异物梗阻超时恶化/昏倒）
- GET  /api/chat/history 训练历史（会话 + 评分摘要）
- DELETE /api/chat/session/{id} 删除当前用户的一次完整训练记录
- POST /api/chat/restart-stage 重新开始当前阶段
- POST /api/chat/end 结束对话

架构（见《“易”生伴 功能描述》多智能体设计）：
- 患者智能体：扮演患者/医生等角色，用 app/ai/prompts.py 的提示词 + call_llm 生成回复
- 教练智能体：实时评价用户行为（提示/警告/干预），返回 JSON
- 两者并行调用，互不阻塞，保证响应时间

参考实现见 frontend/src/api/chat.js 的注释
"""
import asyncio
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.schemas import (
    MedicalRecordRequest,
    StartChatRequest,
    StartChatResponse,
    SendMessageRequest,
    SendMessageResponse,
    SceneInfo,
)
from app.models import User, Scene, ChatSession, ChatMessage, Result
from app.database import get_db
from app.routers.auth import get_current_user
from app.ai import llm
from app.ai.prompts import (
    STAGE_CATALOG,
    build_coach_qa_prompt,
    build_coach_system_prompt,
    build_patient_system_prompt,
    build_stage_judge_system_prompt,
    get_initial_stage,
    get_scene_type,
)
from app.ai.scenario_generator import generate_scene_context
from app.usage import ensure_quota, record_usage

router = APIRouter(prefix="/api/chat", tags=["对话"])
logger = logging.getLogger(__name__)


# =====================================================
# 工具函数
# =====================================================
def _get_owned_session(db: Session, session_id: int, user: User) -> ChatSession:
    """查询属于当前用户的会话，不存在或越权返回 404"""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return session


def _get_scene(db: Session, scene_id: int) -> Scene:
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    return scene


from app.voice import verify_assessments, with_voice


def _history_for_llm(messages) -> list:
    """把数据库消息转成大模型对话历史（coach 消息不参与角色扮演）"""
    start_index = 0
    for index, message in enumerate(messages):
        if message.role == "system" and message.extra and message.extra.get("kind") == "stage_restart":
            start_index = index + 1
    history = []
    for m in messages[start_index:]:
        # 向教练的提问与病历草稿不参与患者角色扮演，避免患者把病历当成新问题回答。
        if m.role == "user" and not (
            m.extra and m.extra.get("kind") in ("coach_q", "medical_record")
        ):
            history.append({"role": "user", "content": with_voice(m.content, (m.extra or {}).get('voice_assessments'))})
        elif m.role == "ai" and not (m.extra and m.extra.get("superseded")):
            history.append({"role": "assistant", "content": m.content})
    return history


def _recent_scene_contexts(db: Session, user_id: int, scene_id: int) -> list[dict]:
    """读取最近三次同场景配置，供场景生成去重。"""
    recent = (
        db.query(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(
            ChatSession.user_id == user_id,
            ChatSession.scene_id == scene_id,
            ChatMessage.role == "system",
        )
        .order_by(ChatMessage.id.desc())
        .limit(3)
        .all()
    )
    return [
        item.extra.get("scene_context")
        for item in reversed(recent)
        if item.extra and isinstance(item.extra.get("scene_context"), dict)
    ]


def _coach_history_for_llm(messages) -> list:
    """教练问答的对话历史：保留完整角色扮演脉络 + 之前与教练的问答，
    让学生可以基于上一条追问，而不是每次新开话题。"""
    history = []
    for m in messages:
        if m.extra and m.extra.get("superseded"):
            continue
        if m.role == "user":
            if m.extra and m.extra.get("kind") == "coach_q":
                history.append({"role": "user", "content": with_voice(f"[向教练提问] {m.content}", (m.extra or {}).get('voice_assessments'))})
            elif m.extra and m.extra.get("kind") == "medical_record":
                continue
            else:
                history.append({"role": "user", "content": with_voice(m.content, (m.extra or {}).get('voice_assessments'))})
        elif m.role == "ai":
            history.append({"role": "assistant", "content": m.content})
        elif m.role == "coach" and m.extra and m.extra.get("kind") == "coach_answer":
            history.append({"role": "assistant", "content": m.content})
    return history


def _session_context(messages) -> dict:
    for message in messages:
        if message.role == "system" and message.extra:
            context = message.extra.get("scene_context")
            if isinstance(context, dict):
                return context
    return {}


def _context_with_runtime_state(messages, context: dict, current_user: User) -> dict:
    """把每轮变化的状态显式传给患者、教练与阶段智能体。"""
    latest_record = next(
        (
            message for message in reversed(messages)
            if message.role == "user" and message.extra and message.extra.get("kind") == "medical_record"
        ),
        None,
    )
    return {
        **(context or {}),
        "trainee_profile": {
            "school": current_user.school or "",
            "real_name": current_user.real_name or "",
        },
        "medical_record_status": {
            "saved": bool(latest_record),
            "saved_at": _to_ms(latest_record.timestamp) if latest_record and latest_record.timestamp else None,
            "version": int((latest_record.extra or {}).get("record_version", 0)) if latest_record else 0,
            "latest_content": latest_record.content.removeprefix("【病历记录】\n") if latest_record else "",
        },
    }


def _latest_stage_info(messages, scene_type: str) -> dict:
    for message in reversed(messages):
        if (
            message.extra
            and message.extra.get("kind") != "medical_record"
            and not message.extra.get("superseded")
            and isinstance(message.extra.get("stage_info"), dict)
        ):
            return message.extra["stage_info"]
    return get_initial_stage(scene_type)


def _normalize_stage_info(payload: dict | None, scene_type: str, current: dict) -> dict:
    stages = STAGE_CATALOG.get(scene_type) or STAGE_CATALOG["first_visit"]
    stage_by_id = {item["id"]: item for item in stages}
    try:
        stage_id = int((payload or {}).get("stage", current.get("id", stages[0]["id"])))
    except (TypeError, ValueError):
        stage_id = int(current.get("id", stages[0]["id"]))
    if stage_id not in stage_by_id:
        stage_id = int(current.get("id", stages[0]["id"]))

    try:
        progress = int((payload or {}).get("progress", current.get("progress", 0)))
    except (TypeError, ValueError):
        progress = int(current.get("progress", 0))

    definition = stage_by_id[stage_id]
    previous_id = int(current.get("id", stages[0]["id"]))
    return {
        **definition,
        "progress": max(0, min(100, progress)),
        "transitioned": stage_id != previous_id,
        # 只信阶段智能体的明确判定（收尾必须完成），到达最后阶段本身不算完成
        "finished": bool((payload or {}).get("finished")),
        "reason": str((payload or {}).get("reason") or "根据当前对话更新进度")[:80],
        "total": len(stages),
    }


def _fallback_stage_info(messages, scene_type: str, current: dict) -> dict:
    """阶段智能体不可用时的保守判断，不会跳过多个阶段。"""
    user_text = " ".join(message.content for message in messages if message.role == "user")
    ai_text = " ".join(message.content for message in messages if message.role == "ai")
    system_text = " ".join(message.content for message in messages if message.role == "system")
    all_text = " ".join((system_text, user_text, ai_text))
    current_id = int(current.get("id", 1))
    next_id = current_id
    progress = 40 if user_text else 0

    if scene_type == "choking":
        if current_id == 1 and any(word in user_text for word in ("完全梗阻", "不能说话", "拍背", "海姆立克", "腹部冲击")):
            next_id, progress = 2, 10
        if any(word in ai_text for word in ("咳出", "异物排出", "大口喘气")):
            next_id, progress = 3, 10
    elif scene_type == "osce":
        dialogue_text = " ".join(
            message.content
            for message in messages
            if message.role == "user" and not (message.extra and message.extra.get("kind") == "medical_record")
        )
        record_messages = [
            message for message in messages
            if message.role == "user" and message.extra and message.extra.get("kind") == "medical_record"
        ]
        opening_done = any(word in dialogue_text for word in ("您好", "你好", "医生", "姓名", "名字", "配合", "同意"))
        hpi_groups = (
            ("哪里不舒服", "主要不适", "怎么了", "主诉"),
            ("多久", "什么时候", "起病", "开始"),
            ("性质", "程度", "加重", "缓解", "诱因"),
            ("伴随", "还有", "有没有"),
            ("治疗", "检查过", "吃过药", "诊治"),
            ("睡眠", "食欲", "大小便", "体重", "精神"),
        )
        hpi_done = sum(any(word in dialogue_text for word in group) for group in hpi_groups) >= 4
        other_history = sum(
            word in dialogue_text
            for word in ("既往", "过敏", "手术", "输血", "个人史", "月经", "婚育", "家族")
        ) >= 3
        exam_requested = any(
            word in dialogue_text
            for word in ("生命体征", "查体", "体格检查", "听诊", "心电图", "超声", "胸片", "血常规")
        )
        if current_id == 1 and opening_done:
            next_id, progress = 2, 10
        elif current_id == 2 and hpi_done:
            next_id, progress = 3, 10
        elif current_id == 3 and other_history:
            next_id, progress = 4, 10
        elif current_id == 4 and exam_requested:
            # 查体/辅助检查是快速过渡，不要求学生逐项操作。
            next_id, progress = 5, 10
        elif current_id == 5 and record_messages:
            next_id, progress = 5, 100
    else:
        registration = any(word in user_text for word in ("挂号", "预约", "智能分诊", "智能问诊", "智能导诊", "科"))
        printed_report = "报到单" in user_text and any(word in user_text for word in ("自助机", "打印", "打出"))
        clinic_scan = "报到机" in user_text and any(word in user_text for word in ("诊间", "扫码", "扫描", "报到"))
        emergency_triage = "急诊" in user_text and any(word in user_text for word in ("分诊", "评估", "护士"))
        diagnosis_or_order = any(
            word in ai_text
            for word in ("诊断", "考虑是", "给你开", "处方", "检查单", "治疗项目")
        )
        manual_window = any(word in user_text for word in ("人工收费窗口", "人工缴费窗口", "人工窗口", "收费窗口"))
        paid = any(word in user_text for word in ("缴费", "付费", "支付", "医保", "自费", "付钱"))
        order_executed = any(
            word in ai_text + user_text
            for word in ("取药", "领药", "药师", "完成检查", "做检查", "接受治疗", "治疗完成")
        )
        emergency_case = any(
            word in all_text
            for word in ("急危重症", "脑出血", "脑卒中", "意识障碍", "严重呼吸困难", "大出血", "休克", "生命危险", "绿色通道", "从未有过的剧烈头痛")
        )
        emergency_care_started = any(
            word in ai_text + user_text
            for word in ("绿色通道", "紧急检查", "立即检查", "头颅CT", "抢救", "紧急手术", "立即手术", "直接治疗", "先治疗")
        )
        emergency_care_completed = any(
            word in ai_text + user_text
            for word in ("病情稳定", "抢救成功", "手术完成", "术后", "治疗完成", "已完成检查")
        )

        # 普通门诊必须先完成打印报到单和诊间扫码；急症分诊不受此限制。
        if current_id == 1 and (emergency_triage or (registration and printed_report and clinic_scan)):
            next_id, progress = 2, 10
        elif current_id == 2 and diagnosis_or_order:
            next_id, progress = 3, 10
        elif current_id == 3 and ((emergency_case and emergency_care_started) or (manual_window and paid)):
            next_id, progress = 4, 10
        elif current_id == 4 and (
            (emergency_case and emergency_care_completed)
            or (not emergency_case and manual_window and paid and order_executed)
        ):
            next_id, progress = 5, 10

    return _normalize_stage_info(
        {"stage": next_id, "progress": progress, "reason": "本地规则保守判断"},
        scene_type,
        current,
    )


_CHOKING_RECOVERY_MARKERS = (
    "咳出异物",
    "把异物咳出",
    "异物排出",
    "异物已排出",
    "吐出异物",
    "异物吐出",
    "恢复了呼吸",
    "恢复正常呼吸",
    "能够正常呼吸",
    "可以正常呼吸",
    "呼吸逐渐恢复",
    "大口喘气",
)
_CHOKING_UNRESOLVED_MARKERS = (
    "未咳出异物",
    "没咳出异物",
    "没有咳出异物",
    "异物未排出",
    "异物没有排出",
    "异物仍未排出",
    "仍无法呼吸",
    "继续窒息",
)


def _choking_pressure_resolved(messages, stage_info: dict | None = None) -> bool:
    """只有患者明确咳出异物并恢复呼吸后才停止倒计时。

    开始拍背/腹部冲击代表进入抢救过程，并不等于脱险；阶段判断也可能提前，
    因此不能再用“已施救”或阶段编号解除时间压力。
    """
    for message in reversed(messages):
        if message.role != "ai":
            continue
        # “仍未咳出异物”包含“咳出异物”子串，必须先排除否定表达。
        if any(marker in message.content for marker in _CHOKING_UNRESOLVED_MARKERS):
            return False
        if any(marker in message.content for marker in _CHOKING_RECOVERY_MARKERS):
            return True
    return False


def _time_pressure_status(session: ChatSession, scene_type: str, context: dict, messages) -> str | None:
    if scene_type != "choking" or not session.started_at:
        return None
    current_stage = _latest_stage_info(messages, scene_type)
    if _choking_pressure_resolved(messages, current_stage):
        return None

    elapsed = max(0, int((datetime.utcnow() - session.started_at).total_seconds()))
    deterioration_after = int(context.get("deterioration_after", 75))
    collapse_after = int(context.get("collapse_after", 165))
    if elapsed >= collapse_after:
        return "用户长时间未采取有效急救，患者已经失去意识、无正常呼吸；按规则转入CPR处置。"
    if elapsed >= deterioration_after:
        return "用户尚未采取有效急救，患者眼神涣散、身体开始摇晃，表现正在恶化。"
    return None


def _build_ui_action(scene_type: str, user_text: str, coach_json: dict | None) -> dict | None:
    if scene_type == "choking" and "海姆立克" in user_text:
        action_details = ("身后", "肚脐", "肋弓", "向内", "向上", "冲击")
        if sum(detail in user_text for detail in action_details) < 3:
            return {
                "type": "describe_action",
                "title": "请具体描述急救动作",
                "description": "只说方法名称还不够，请补全体位、手位和用力方向。",
                "fields": [
                    {"key": "position", "label": "你站在哪里？", "placeholder": "请输入"},
                    {"key": "hand", "label": "手放在哪里？", "placeholder": "请输入"},
                    {"key": "force", "label": "如何用力？", "placeholder": "请输入"},
                ],
            }
    if coach_json and coach_json.get("should_intervene"):
        return {"type": "coach_intervention", "title": "观察者教练已介入"}
    return None


def _public_message_extra(message: ChatMessage) -> dict | None:
    """过滤只供后端智能体使用的答案字段。"""
    if not message.extra:
        return None
    if message.role == "system":
        return {
            "display": message.extra.get("display") or {},
            "stage_info": message.extra.get("stage_info"),
        }
    if message.role == "coach":
        return {
            "type": message.extra.get("type", "info"),
            "kind": message.extra.get("kind"),
            "should_intervene": bool(message.extra.get("should_intervene")),
            "superseded": bool(message.extra.get("superseded")),
        }
    if message.role == "ai":
        return {
            "kind": message.extra.get("kind"),
            "stage_info": message.extra.get("stage_info"),
            "attachments": message.extra.get("attachments") or [],
            "airway_state": message.extra.get("airway_state"),
            "speech_text": message.extra.get("speech_text") or "",
            "superseded": bool(message.extra.get("superseded")),
        }
    if message.role == "user" and message.extra.get("kind") == "medical_record":
        return {
            "kind": "medical_record",
            "record_version": int(message.extra.get("record_version", 1)),
        }
    return None


def _to_ms(dt: datetime) -> int:
    """datetime → 毫秒时间戳（前端约定）。

    存储用的是 naive UTC（datetime.utcnow），必须先标成 UTC 再转；
    否则会被按本地时区解释，显示时间偏差正好等于时区差（东八区差 8 小时）。
    """
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


_INSURANCE_ATTACHMENT_MARKERS = (
    "【发送资料：南京医科大学医保资料】",
    "[发送资料：南京医科大学医保资料]",
)


def _extract_insurance_attachments(content: str, context: dict) -> tuple[str, list[dict[str, str]]]:
    """把智能体的资料工具标记转换为可点击附件，不展示内部指令。"""
    if not any(marker in content for marker in _INSURANCE_ATTACHMENT_MARKERS):
        return content, []
    cleaned = content
    for marker in _INSURANCE_ATTACHMENT_MARKERS:
        cleaned = cleaned.replace(marker, "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    attachments = [
        {"title": str(item.get("title") or "医保资料"), "url": str(item.get("url") or "")}
        for item in context.get("insurance_resources") or []
        if isinstance(item, dict) and item.get("url")
    ]
    return cleaned, attachments


def _first_mapping(payload) -> dict:
    """Normalize occasionally malformed JSON-agent output without breaking chat."""
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return next((item for item in payload if isinstance(item, dict)), {})
    return {}


def _normalize_choking_patient_reply(payload) -> tuple[str, str, str]:
    """Validate choking state and keep only genuinely speakable patient words."""
    data = _first_mapping(payload)
    airway_state = str(data.get("airway_state") or "blocked").strip().lower()
    if airway_state not in {"blocked", "coughing", "recovered"}:
        airway_state = "blocked"
    display_text = str(data.get("display_text") or "").strip()
    speech_text = str(data.get("speech_text") or "").strip()
    if airway_state != "recovered":
        speech_text = ""
    speech_text = speech_text[:500]
    if not display_text:
        display_text = "（患者仍双手紧紧掐住喉咙，无法说话。）"
    if speech_text and speech_text not in display_text:
        display_text = f"{display_text}\n患者：“{speech_text}”"
    return display_text[:2000], airway_state, speech_text


def _latest_choking_airway_state(messages) -> str:
    """Read the last persisted patient state so a provider failure cannot reset recovery."""
    for message in reversed(messages):
        if getattr(message, "role", None) != "ai":
            continue
        extra = getattr(message, "extra", None) or {}
        airway_state = str(extra.get("airway_state") or "").strip().lower()
        if airway_state in {"blocked", "coughing", "recovered"}:
            return airway_state

        content = str(getattr(message, "content", "") or "")
        if any(marker in content for marker in _CHOKING_UNRESOLVED_MARKERS):
            return "blocked"
        if any(marker in content for marker in _CHOKING_RECOVERY_MARKERS):
            return "recovered"
    return "blocked"


def _fallback_choking_patient_reply(messages) -> tuple[str, str, str]:
    """Keep the choking conversation usable when structured model output is unavailable."""
    airway_state = _latest_choking_airway_state(messages)
    if airway_state == "recovered":
        speech_text = "现在好多了，已经能正常呼吸。我会去医院检查，谢谢你。"
        return (
            f"（患者呼吸已经平稳，点头回应你的关心。）\n患者：“{speech_text}”",
            airway_state,
            speech_text,
        )
    if airway_state == "coughing":
        return "（患者仍在用力咳嗽，暂时说不出完整的话。）", airway_state, ""
    return "（患者仍双手紧紧掐住喉咙，无法说话。）", "blocked", ""


def _should_attach_insurance_resources(user_text: str, context: dict) -> bool:
    """Treat an explicit NJMU insurance question as a tool request even if the model omits its marker."""
    school = str((context.get("trainee_profile") or {}).get("school") or "")
    if "南京医科大学" not in school or not context.get("insurance_resources"):
        return False
    text = user_text.strip()
    insurance_intent = any(word in text for word in ("医保", "参保", "报销", "医疗保险"))
    asks_for_help = any(word in text for word in (
        "不了解", "不清楚", "不知道", "怎么", "如何", "政策", "资料", "文件", "依据", "能不能", "可以吗", "请问",
    ))
    return insurance_intent and asks_for_help


def _insurance_resource_cards(context: dict) -> list[dict[str, str]]:
    return [
        {"title": str(item.get("title") or "医保资料"), "url": str(item.get("url") or "")}
        for item in context.get("insurance_resources") or []
        if isinstance(item, dict) and item.get("url")
    ]


# =====================================================
# ✅ 已实现：POST /api/chat/start
# =====================================================
@router.post("/start", response_model=StartChatResponse)
async def start_chat(
    data: StartChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    开始一个新对话会话

    逻辑：
    1. 查询场景 → 404
    2. 创建 ChatSession 记录
    3. 把开场白作为第一条 ai 消息入库（对话回放需要）
    4. 返回 session_id + 开场白 + 场景信息
    """
    scene = _get_scene(db, data.scene_id)
    ensure_quota(db, current_user)

    scene_type = get_scene_type(scene)
    previous_contexts = _recent_scene_contexts(db, current_user.id, scene.id)
    generated = await asyncio.to_thread(
        generate_scene_context,
        scene,
        scene_type,
        data.gender,
        previous_contexts,
    )
    record_usage(db, current_user, "场景生成上下文" * 300, generated.get("opening_message", ""))
    initial_stage = get_initial_stage(scene_type)
    initial_stage["total"] = len(STAGE_CATALOG.get(scene_type) or STAGE_CATALOG["first_visit"])

    session = ChatSession(user_id=current_user.id, scene_id=scene.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    opening = generated["opening_message"]
    db.add(ChatMessage(
        session_id=session.id,
        role="system",
        content=opening,
        extra={
            "display": generated["opening_meta"],
            "scene_context": generated["context"],
            "stage_info": initial_stage,
        },
    ))
    db.commit()

    scene_info = SceneInfo.model_validate(scene)
    if scene_type == "first_visit":
        scene_info = scene_info.model_copy(update={"role": "医院流程角色"})
    elif scene_type == "osce":
        scene_info = scene_info.model_copy(update={"role": "标准化患者"})

    return StartChatResponse(
        session_id=session.id,
        opening_message=opening,
        opening_role="system",
        opening_meta=generated["opening_meta"],
        scene_info=scene_info,
    )


# =====================================================
# ✅ 已实现：POST /api/chat/message
# =====================================================
@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息并获取 AI 回复

    逻辑：
    1. 校验会话归属、会话未结束
    2. 保存用户消息
    3. 并行调用患者智能体（生成回复）+ 教练智能体（实时评价）
    4. 保存 AI 消息；教练干预时额外保存 coach 消息
    5. 返回 AI 回复 + 教练提示
    """
    session = _get_owned_session(db, data.session_id, current_user)
    if session.ended_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话已结束")

    scene = _get_scene(db, session.scene_id)
    scene_type = get_scene_type(scene)
    ensure_quota(db, current_user)

    if data.supersede_previous_ai:
        previous_user = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id, ChatMessage.role == "user")
            .order_by(ChatMessage.id.desc())
            .first()
        )
        previous_ai = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id, ChatMessage.role == "ai")
            .order_by(ChatMessage.id.desc())
            .first()
        )
        # 只废弃上一条用户消息之后生成的回复；若上一轮失败，不误伤更早的正常回复。
        if previous_ai and previous_user and previous_ai.id > previous_user.id:
            previous_ai.extra = {**(previous_ai.extra or {}), "superseded": True}
            following_coaches = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.session_id == session.id,
                    ChatMessage.role == "coach",
                    ChatMessage.id > previous_ai.id,
                )
                .all()
            )
            for coach in following_coaches:
                coach.extra = {**(coach.extra or {}), "superseded": True}
            db.commit()

    # 1. 保存用户消息
    voice_assessments = verify_assessments(data.voice_receipts, current_user.id, f'chat:{session.id}')
    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message, extra={'voice_assessments': voice_assessments} if voice_assessments else None)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. 组装对话历史（含刚存的用户消息）
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = _history_for_llm(messages)
    session_context = _context_with_runtime_state(messages, _session_context(messages), current_user)
    current_stage = _latest_stage_info(messages, scene_type)
    time_pressure = _time_pressure_status(session, scene_type, session_context, messages)

    # 3. 并行调用患者智能体 + 教练智能体
    patient_prompt = build_patient_system_prompt(
        scene, scene_type, session_context, current_stage, time_pressure
    )
    coach_prompt = build_coach_system_prompt(scene, scene_type, session_context, current_stage)
    stage_prompt = build_stage_judge_system_prompt(
        scene, scene_type, session_context, current_stage
    )

    async def call_patient():
        if scene_type == "choking":
            try:
                payload = await asyncio.to_thread(
                    llm.call_llm_json, history, patient_prompt, llm.CHAT_REASONING_EFFORT
                )
                return _normalize_choking_patient_reply(payload)
            except Exception:
                logger.exception(
                    "Structured choking patient reply failed; using persisted airway-state fallback"
                )
                return _fallback_choking_patient_reply(messages)
        return await asyncio.to_thread(llm.generate_reply, patient_prompt, history)

    async def call_coach():
        # 教练每轮都要跑，用低推理力度保证响应速度（和患者智能体并行）
        return await asyncio.to_thread(
            llm.call_llm_json, history, coach_prompt, llm.CHAT_REASONING_EFFORT
        )

    async def call_stage_judge():
        return await asyncio.to_thread(
            llm.call_llm_json, history, stage_prompt, llm.CHAT_REASONING_EFFORT
        )

    patient_task = asyncio.create_task(call_patient())
    coach_task = asyncio.create_task(call_coach())
    stage_task = asyncio.create_task(call_stage_judge())

    # 患者回复是主链路，失败则整体失败
    try:
        patient_result = await patient_task
        if scene_type == "choking":
            ai_content, airway_state, speech_text = patient_result
        else:
            ai_content, airway_state, speech_text = patient_result, None, None
    except Exception as e:
        coach_task.cancel()
        stage_task.cancel()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 回复生成失败：{e}",
        )

    # 教练提示是辅助链路，失败不影响对话（coach_tip 为 None）
    coach_tip = None
    coach_json = None
    try:
        coach_json = _first_mapping(await coach_task)
    except Exception:
        pass

    try:
        stage_json = _first_mapping(await stage_task)
        stage_info = _normalize_stage_info(stage_json, scene_type, current_stage)
    except Exception:
        stage_info = _fallback_stage_info(messages, scene_type, current_stage)

    ai_content, attachments = _extract_insurance_attachments(ai_content, session_context)
    if not attachments and _should_attach_insurance_resources(data.message, session_context):
        attachments = _insurance_resource_cards(session_context)

    # 4. 保存 AI 消息
    ai_msg = ChatMessage(
        session_id=session.id,
        role="ai",
        content=ai_content,
        extra={
            "stage_info": stage_info,
            "attachments": attachments,
            "airway_state": airway_state,
            "speech_text": speech_text,
        },
    )
    db.add(ai_msg)

    # 5. 处理教练提示
    coach_msg = None
    if coach_json:
        hint = (coach_json.get("hint") or "").strip()
        hint_type = coach_json.get("hint_type") or "info"
        should_intervene = bool(coach_json.get("should_intervene"))
        intervention = (coach_json.get("intervention") or "").strip()

        if should_intervene and (intervention or hint):
            coach_tip = {"type": "error", "text": intervention or hint}
            coach_msg = ChatMessage(
                session_id=session.id,
                role="coach",
                content=intervention or hint,
                extra={"type": "error", "hint": hint, "should_intervene": True},
            )
        elif hint:
            type_map = {"good": "success", "warn": "warning", "error": "error"}
            coach_tip = {"type": type_map.get(hint_type, "info"), "text": hint}
            coach_msg = ChatMessage(
                session_id=session.id,
                role="coach",
                content=hint,
                extra={"type": coach_tip["type"], "should_intervene": False},
            )

        if coach_msg:
            db.add(coach_msg)

    db.commit()
    db.refresh(ai_msg)
    if coach_msg and coach_tip:
        db.refresh(coach_msg)
        coach_tip.update({
            "id": coach_msg.id,
            "timestamp": _to_ms(coach_msg.timestamp),
        })

    quota_info = record_usage(
        db,
        current_user,
        patient_prompt + coach_prompt + stage_prompt + json.dumps(history, ensure_ascii=False) * 3,
        ai_content + json.dumps(coach_json or {}, ensure_ascii=False) + json.dumps(stage_info or {}, ensure_ascii=False),
    )
    return SendMessageResponse(
        message_id=ai_msg.id,
        role="ai",
        content=ai_content,
        timestamp=_to_ms(ai_msg.timestamp),
        coach_tip=coach_tip,
        stage_info=stage_info,
        ui_action=_build_ui_action(scene_type, data.message, coach_json),
        quota=quota_info,
        attachments=attachments,
        airway_state=airway_state,
        speech_text=speech_text,
    )


# =====================================================
# POST /api/chat/record 保存 OSCE 学生病历
# =====================================================
@router.post("/record")
async def save_medical_record(
    data: MedicalRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存或更新学生独立书写的 OSCE 病历，并将其纳入最终评分。"""
    session = _get_owned_session(db, data.session_id, current_user)
    if session.ended_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话已结束")

    scene = _get_scene(db, session.scene_id)
    if get_scene_type(scene) != "osce":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅 OSCE 场景支持病历记录")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    current = _latest_stage_info(messages, "osce")
    required_sections = ("基本信息", "主诉", "现病史", "其他病史", "体格检查", "辅助检查", "病历摘要", "初步诊断")

    def section_has_content(section: str) -> bool:
        start = data.content.find(section)
        if start < 0:
            return False
        body_start = start + len(section)
        following = [
            data.content.find(other, body_start)
            for other in required_sections
            if other != section and data.content.find(other, body_start) >= 0
        ]
        end = min(following) if following else len(data.content)
        body = data.content[body_start:end].lstrip("：: \n\t（）()")
        return len("".join(body.split())) >= 3

    completed_sections = [section for section in required_sections if section_has_content(section)]
    record_progress = min(100, round(len(completed_sections) / len(required_sections) * 100))
    stage_info = {
        **current,
        "transitioned": False,
        "finished": False,
        "reason": "病历草稿已更新，继续按当前问诊阶段训练",
        "total": len(STAGE_CATALOG["osce"]),
    }
    stored_content = f"【病历记录】\n{data.content}"
    record = next(
        (
            message for message in reversed(messages)
            if message.role == "user" and message.extra and message.extra.get("kind") == "medical_record"
        ),
        None,
    )
    if record:
        next_version = int((record.extra or {}).get("record_version", 1)) + 1
        record.content = stored_content
        record.timestamp = datetime.utcnow()
        record.extra = {
            "kind": "medical_record",
            "record_version": next_version,
            "completed_sections": completed_sections,
        }
    else:
        next_version = 1
        record = ChatMessage(
            session_id=session.id,
            role="user",
            content=stored_content,
            extra={
                "kind": "medical_record",
                "record_version": next_version,
                "completed_sections": completed_sections,
            },
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "message_id": record.id,
        "content": data.content,
        "timestamp": _to_ms(record.timestamp),
        "completed_sections": completed_sections,
        "record_progress": record_progress,
        "record_version": next_version,
        "stage_info": stage_info,
    }


# =====================================================
# ✅ 已实现：GET /api/chat/session/{session_id}
# =====================================================
@router.get("/session/{session_id}")
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话详情（含全部消息，供对话回放）"""
    session = _get_owned_session(db, session_id, current_user)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    return {
        "session_id": session.id,
        "scene_id": session.scene_id,
        "started_at": _to_ms(session.started_at) if session.started_at else None,
        "ended_at": _to_ms(session.ended_at) if session.ended_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": _to_ms(m.timestamp) if m.timestamp else None,
                "extra": _public_message_extra(m),
            }
            for m in messages
        ],
    }


# =====================================================
# POST /api/chat/restart-stage
# =====================================================
@router.post("/restart-stage")
async def restart_stage(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保留复盘记录，但清空角色扮演上下文并从当前阶段重新练习。"""
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 session_id")
    session = _get_owned_session(db, int(session_id), current_user)
    if session.ended_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话已结束")

    scene = _get_scene(db, session.scene_id)
    scene_type = get_scene_type(scene)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    current_stage = _latest_stage_info(messages, scene_type)
    restarted_stage = {**current_stage, "progress": 0, "transitioned": False, "reason": "用户重新开始本阶段"}
    content = f"已重新开始“{restarted_stage['name']}”阶段。请回到本阶段目标：{restarted_stage['goal']}。"
    message = ChatMessage(
        session_id=session.id,
        role="system",
        content=content,
        extra={
            "kind": "stage_restart",
            "display": {
                "kind": "stage_restart",
                "agent_name": "观察者教练",
                "first_step": restarted_stage["goal"],
                "quick_actions": [],
            },
            "stage_info": restarted_stage,
        },
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "timestamp": _to_ms(message.timestamp),
        "stage_info": restarted_stage,
        "meta": message.extra["display"],
    }


# =====================================================
# POST /api/chat/coach 向观察者教练提问
# =====================================================
@router.post("/coach")
async def ask_coach(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    向观察者教练提问（教练问答）。

    学生可以直接向教练请教医学知识和流程；教练以引导为主，
    不直接替学生做决策。问答会存入消息流（回放可见），
    但向教练的提问不会混入患者智能体的对话历史。
    """
    session_id = data.get("session_id")
    question = (data.get("message") or "").strip()
    if not session_id or not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 session_id 或 message")

    session = _get_owned_session(db, int(session_id), current_user)
    if session.ended_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话已结束")
    ensure_quota(db, current_user)

    scene = _get_scene(db, session.scene_id)
    scene_type = get_scene_type(scene)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    session_context = _context_with_runtime_state(messages, _session_context(messages), current_user)
    current_stage = _latest_stage_info(messages, scene_type)

    voice_assessments = verify_assessments(data.get('voice_receipts', []), current_user.id, f'chat:{session.id}')
    db.add(ChatMessage(
        session_id=session.id,
        role="user",
        content=question,
        extra={"kind": "coach_q", "voice_assessments": voice_assessments},
    ))
    db.commit()

    history = _coach_history_for_llm(messages) + [{"role": "user", "content": with_voice(f"[向教练提问] {question}", voice_assessments)}]
    qa_prompt = build_coach_qa_prompt(scene, scene_type, session_context, current_stage)
    try:
        answer = await asyncio.to_thread(llm.generate_reply, qa_prompt, history)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"教练回复生成失败：{e}")

    coach_msg = ChatMessage(
        session_id=session.id,
        role="coach",
        content=answer,
        extra={"type": "info", "kind": "coach_answer"},
    )
    db.add(coach_msg)
    db.commit()
    db.refresh(coach_msg)
    quota_info = record_usage(
        db,
        current_user,
        qa_prompt + json.dumps(history, ensure_ascii=False),
        answer,
    )

    return {
        "message_id": coach_msg.id,
        "role": "coach",
        "content": answer,
        "timestamp": _to_ms(coach_msg.timestamp),
        "quota": quota_info,
    }


# =====================================================
# GET /api/chat/session/{session_id}/pressure 时间压力轮询
# =====================================================
@router.get("/session/{session_id}/pressure")
async def get_time_pressure(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    时间压力状态轮询（仅异物梗阻场景使用）。

    前端定时调用；异物真正排出前持续计时，超时会出现恶化/昏倒表现，
    每种状态只入库一次（幂等）。开始急救本身不会提前解除时间压力。
    """
    session = _get_owned_session(db, session_id, current_user)
    if session.ended_at:
        return {"status": "ended"}
    if not session.started_at:
        return {"status": "ok"}

    scene = _get_scene(db, session.scene_id)
    scene_type = get_scene_type(scene)
    if scene_type != "choking":
        return {"status": "off"}

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    context = _session_context(messages)
    current_stage = _latest_stage_info(messages, scene_type)

    # 只有患者明确咳出异物并恢复呼吸后才永久停止倒计时；开始施救本身不等于脱险。
    if _choking_pressure_resolved(messages, current_stage):
        return {"status": "resolved"}

    kinds = {
        m.extra.get("kind")
        for m in messages
        if m.extra and m.extra.get("kind") in ("deterioration", "collapse")
    }

    elapsed = max(0, int((datetime.utcnow() - session.started_at).total_seconds()))
    deterioration_after = int(context.get("deterioration_after", 75))
    collapse_after = int(context.get("collapse_after", 165))

    if elapsed >= collapse_after and "collapse" not in kinds:
        msg = ChatMessage(
            session_id=session.id,
            role="ai",
            content="（突然瘫软倒地，失去意识，没有正常呼吸——你错过了黄金急救时间，现在必须立即开始 CPR：胸外按压！）",
            extra={"kind": "collapse"},
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return {"status": "collapsed", "elapsed": elapsed, "collapse_after": collapse_after, "message_id": msg.id, "message": msg.content}

    if elapsed >= deterioration_after and "deterioration" not in kinds and "collapse" not in kinds:
        msg = ChatMessage(
            session_id=session.id,
            role="ai",
            content="（眼神开始涣散，身体摇晃，已经站不太稳了……情况正在恶化！）",
            extra={"kind": "deterioration"},
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return {"status": "deteriorating", "elapsed": elapsed, "collapse_after": collapse_after, "message_id": msg.id, "message": msg.content}

    return {"status": "ok", "elapsed": elapsed, "collapse_after": collapse_after}


# =====================================================
# GET /api/chat/history 训练历史
# =====================================================
@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """训练历史：当前用户最近 50 次会话及评分摘要（最新在前）"""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .limit(50)
        .all()
    )
    if not sessions:
        return []

    scene_ids = {s.scene_id for s in sessions}
    scenes = {s.id: s for s in db.query(Scene).filter(Scene.id.in_(scene_ids)).all()}
    results = {
        r.session_id: r
        for r in db.query(Result).filter(Result.user_id == current_user.id).all()
    }

    history = []
    for s in sessions:
        result = results.get(s.id)
        duration = None
        if s.ended_at and s.started_at:
            duration = int((s.ended_at - s.started_at).total_seconds())
        history.append({
            "session_id": s.id,
            "scene_id": s.scene_id,
            "scene_title": scenes[s.scene_id].title if s.scene_id in scenes else "未知场景",
            "started_at": _to_ms(s.started_at) if s.started_at else None,
            "ended_at": _to_ms(s.ended_at) if s.ended_at else None,
            "duration": duration,
            "is_rated": bool(result),
            "total_score": result.total_score if result else None,
            "accuracy": result.accuracy if result else None,
            "warmth": result.warmth if result else None,
            "decision": result.decision if result else None,
            "is_favorite": bool(s.is_favorite),
            "is_pinned": bool(s.is_pinned),
        })
    return history


@router.patch("/session/{session_id}/flags")
async def update_session_flags(
    session_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user)
    if "is_favorite" in data:
        session.is_favorite = int(bool(data["is_favorite"]))
    if "is_pinned" in data:
        session.is_pinned = int(bool(data["is_pinned"]))
    db.commit()
    return {"session_id": session.id, "updated": True}


@router.get("/history/summary")
async def get_history_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Result, ChatSession, Scene)
        .join(ChatSession, ChatSession.id == Result.session_id)
        .join(Scene, Scene.id == ChatSession.scene_id)
        .filter(Result.user_id == current_user.id)
        .all()
    )
    if not rows:
        return {
            "completed": 0,
            "headline": "完成第一次训练后，这里会形成你的成长总结。",
            "highlights": ["愿意开始训练本身就是很好的第一步。"],
            "opportunities": ["可以从任意一个场景开始，逐步积累自己的训练记录。"],
            "scenes": [],
        }

    scene_scores: dict[str, list[int]] = {}
    total_scores = []
    normalized_dims = {"医学准确性": [], "沟通温度": [], "决策合理性": []}
    for result, _session, scene in rows:
        score = int(result.total_score or 0)
        total_scores.append(score)
        scene_scores.setdefault(scene.title, []).append(score)
        scene_type = get_scene_type(scene)
        maxima = {"osce": (40, 20, 40), "first_visit": (30, 40, 30), "choking": (40, 30, 30)}.get(scene_type, (40, 30, 30))
        for label, value, maximum in zip(normalized_dims, (result.accuracy, result.warmth, result.decision), maxima):
            normalized_dims[label].append(round((int(value or 0) / maximum) * 100))

    scene_rows = [
        {"scene": title, "count": len(scores), "average": round(sum(scores) / len(scores))}
        for title, scores in scene_scores.items()
    ]
    scene_rows.sort(key=lambda item: (-item["average"], item["scene"]))
    dimension_avg = {key: round(sum(values) / len(values)) for key, values in normalized_dims.items() if values}
    strongest = max(dimension_avg, key=dimension_avg.get)
    growable = min(dimension_avg, key=dimension_avg.get)
    average = round(sum(total_scores) / len(total_scores))
    return {
        "completed": len(rows),
        "average": average,
        "headline": f"你已经完成{len(rows)}次训练，综合平均{average}分，持续练习的节奏很好。",
        "highlights": [
            f"{strongest}是目前最稳定的优势，平均完成度{dimension_avg[strongest]}%。",
            f"在“{scene_rows[0]['scene']}”中的表现尤其突出，平均{scene_rows[0]['average']}分。",
        ],
        "opportunities": [
            f"{growable}还可以更好；下一轮可在做决定前多用一句话说明依据。",
            "不同场景之间交替练习，可以让已经掌握的能力变得更稳定。",
        ],
        "scenes": scene_rows,
    }


def _delete_session_records(db: Session, session: ChatSession) -> dict[str, int]:
    """显式删除会话关联数据；当前模型未声明 ORM 级联关系。"""
    result_count = (
        db.query(Result)
        .filter(Result.session_id == session.id)
        .delete(synchronize_session=False)
    )
    message_count = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .delete(synchronize_session=False)
    )
    db.delete(session)
    return {"messages": message_count, "results": result_count}


# =====================================================
# DELETE /api/chat/session/{session_id} 删除训练记录
# =====================================================
@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除当前用户的一次会话，以及该会话的消息和评分。"""
    session = _get_owned_session(db, session_id, current_user)
    deleted = _delete_session_records(db, session)
    db.commit()
    return {"session_id": session_id, "deleted": True, **deleted}


# =====================================================
# ✅ 已实现：POST /api/chat/end
# =====================================================
@router.post("/end")
async def end_chat(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    结束对话，准备评分

    逻辑：
    1. 校验会话归属
    2. 记录结束时间（幂等：已结束不重复更新）
    3. 评分在 GET /api/result/{session_id} 中懒加载生成
    """
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 session_id")

    session = _get_owned_session(db, int(session_id), current_user)

    if not session.ended_at:
        session.ended_at = datetime.utcnow()
        db.commit()

    return {"session_id": session.id, "ready_for_rating": True}
