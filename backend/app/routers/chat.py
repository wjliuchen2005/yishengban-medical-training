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

router = APIRouter(prefix="/api/chat", tags=["对话"])


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
            history.append({"role": "user", "content": m.content})
        elif m.role == "ai":
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
        if m.role == "user":
            if m.extra and m.extra.get("kind") == "coach_q":
                history.append({"role": "user", "content": f"[向教练提问] {m.content}"})
            else:
                history.append({"role": "user", "content": m.content})
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


def _latest_stage_info(messages, scene_type: str) -> dict:
    for message in reversed(messages):
        if message.extra and isinstance(message.extra.get("stage_info"), dict):
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
        registration = any(word in user_text for word in ("挂号", "预约", "智能问诊", "智能导诊", "科"))
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


_PRESSURE_ACTIONS = ("拍背", "海姆立克", "腹部冲击", "胸部冲击", "CPR", "心肺复苏")
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
    """患者已获救或施救已开始时，停止“未施救”倒计时。"""
    try:
        if int((stage_info or {}).get("id", 1)) >= 3:
            return True
    except (TypeError, ValueError):
        pass

    user_text = " ".join(message.content for message in messages if message.role == "user")
    if any(word in user_text for word in _PRESSURE_ACTIONS):
        return True

    # 阶段智能体可能比患者回复晚一拍；患者已明确恢复时不能再补写“倒地”。
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
    collapse_after = int(context.get("collapse_after", 135))
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
        }
    if message.role == "ai":
        return {"kind": message.extra.get("kind"), "stage_info": message.extra.get("stage_info")}
    if message.role == "user" and message.extra.get("kind") == "medical_record":
        return {
            "kind": "medical_record",
            "stage_info": message.extra.get("stage_info"),
        }
    return None


def _to_ms(dt: datetime) -> int:
    """datetime → 毫秒时间戳（前端约定）。

    存储用的是 naive UTC（datetime.utcnow），必须先标成 UTC 再转；
    否则会被按本地时区解释，显示时间偏差正好等于时区差（东八区差 8 小时）。
    """
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


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

    scene_type = get_scene_type(scene)
    previous_contexts = _recent_scene_contexts(db, current_user.id, scene.id)
    generated = await asyncio.to_thread(
        generate_scene_context,
        scene,
        scene_type,
        data.gender,
        previous_contexts,
    )
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

    # 1. 保存用户消息
    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
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
    session_context = _session_context(messages)
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
        ai_content = await patient_task
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
        coach_json = await coach_task
    except Exception:
        pass

    try:
        stage_json = await stage_task
        stage_info = _normalize_stage_info(stage_json, scene_type, current_stage)
    except Exception:
        stage_info = _fallback_stage_info(messages, scene_type, current_stage)

    # 4. 保存 AI 消息
    ai_msg = ChatMessage(
        session_id=session.id,
        role="ai",
        content=ai_content,
        extra={"stage_info": stage_info},
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

    return SendMessageResponse(
        message_id=ai_msg.id,
        role="ai",
        content=ai_content,
        timestamp=_to_ms(ai_msg.timestamp),
        coach_tip=coach_tip,
        stage_info=stage_info,
        ui_action=_build_ui_action(scene_type, data.message, coach_json),
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
    required_sections = ("主诉", "现病史", "其他病史", "体格检查", "辅助检查", "病历摘要", "初步诊断")

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
    core_complete = all(section_has_content(section) for section in ("主诉", "现病史", "初步诊断"))
    stage_info = {
        **STAGE_CATALOG["osce"][-1],
        "progress": min(100, round(len(completed_sections) / len(required_sections) * 100)),
        "transitioned": int(current.get("id", 1)) < 5,
        "finished": core_complete,
        "reason": "已保存病历记录" if core_complete else "病历仍需补齐主诉、现病史和初步诊断",
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
        record.content = stored_content
        record.timestamp = datetime.utcnow()
        record.extra = {"kind": "medical_record", "stage_info": stage_info}
    else:
        record = ChatMessage(
            session_id=session.id,
            role="user",
            content=stored_content,
            extra={"kind": "medical_record", "stage_info": stage_info},
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "message_id": record.id,
        "content": data.content,
        "timestamp": _to_ms(record.timestamp),
        "completed_sections": completed_sections,
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

    scene = _get_scene(db, session.scene_id)
    scene_type = get_scene_type(scene)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    session_context = _session_context(messages)
    current_stage = _latest_stage_info(messages, scene_type)

    db.add(ChatMessage(
        session_id=session.id,
        role="user",
        content=question,
        extra={"kind": "coach_q"},
    ))
    db.commit()

    history = _coach_history_for_llm(messages) + [{"role": "user", "content": f"[向教练提问] {question}"}]
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

    return {
        "message_id": coach_msg.id,
        "role": "coach",
        "content": answer,
        "timestamp": _to_ms(coach_msg.timestamp),
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

    前端定时调用；超时未施救时患者智能体会主动出现恶化/昏倒表现，
    每种状态只入库一次（幂等）。已开始急救或进入最后阶段后不再恶化。
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

    # 已开始有效急救、进入后续处理，或患者已明确恢复 → 永久停止倒计时
    if _choking_pressure_resolved(messages, current_stage):
        return {"status": "resolved"}

    kinds = {
        m.extra.get("kind")
        for m in messages
        if m.extra and m.extra.get("kind") in ("deterioration", "collapse")
    }

    elapsed = max(0, int((datetime.utcnow() - session.started_at).total_seconds()))
    deterioration_after = int(context.get("deterioration_after", 75))
    collapse_after = int(context.get("collapse_after", 135))

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
        return {"status": "collapsed", "elapsed": elapsed, "message_id": msg.id, "message": msg.content}

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
        return {"status": "deteriorating", "elapsed": elapsed, "message_id": msg.id, "message": msg.content}

    return {"status": "ok", "elapsed": elapsed}


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
        })
    return history


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
