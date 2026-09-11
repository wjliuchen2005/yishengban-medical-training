"""
评分相关路由

✅ 已实现：
- GET  /api/result/{sessionId} 获取评分结果（懒加载：首次请求在后台线程调用评分智能体，
  立即返回 pending，前端轮询直到评分落库）

同时提供 POST /api/result/{sessionId}/share 生成站内结果链接。

评分逻辑（见《“易”生伴 功能描述》第4节）：
- 医学准确性 / 沟通温度 / 决策合理性 三维度（各场景分值配比不同）
- 由评分智能体（大模型）根据完整对话记录打分，结果存 results 表
"""
import logging
import os
import threading
import time
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, Scene, ChatSession, ChatMessage, Result
from app.database import get_db, SessionLocal
from app.routers.auth import get_current_user
from app.ai import llm
from app.ai.prompts import build_scorer_system_prompt, get_scene_type
from app.voice import with_voice

router = APIRouter(prefix="/api/result", tags=["评分"])

logger = logging.getLogger(__name__)

# 评分请求必须比 SDK 默认超时短，断网时尽快进入本地规则保底评分。
try:
    RATING_REQUEST_TIMEOUT_SECONDS = max(5.0, float(os.getenv("RATING_REQUEST_TIMEOUT_SECONDS", "60")))
except ValueError:
    RATING_REQUEST_TIMEOUT_SECONDS = 60.0
try:
    RATING_TASK_STALE_SECONDS = max(
        RATING_REQUEST_TIMEOUT_SECONDS + 15.0,
        float(os.getenv("RATING_TASK_STALE_SECONDS", "90")),
    )
except ValueError:
    RATING_TASK_STALE_SECONDS = max(RATING_REQUEST_TIMEOUT_SECONDS + 15.0, 90.0)

# 后台评分任务注册表：session_id -> 任务令牌（monotonic 开始时间）。
# 带时间而不是只存 session_id，才能在进程内识别并恢复卡死任务。
_rating_tasks: dict[int, float] = {}
_rating_lock = threading.Lock()


def _claim_rating_task(session_id: int, now: float | None = None) -> tuple[float, bool] | None:
    """登记评分任务；陈旧任务可被新任务接管，并标记为只走快速保底评分。"""
    started_at = time.monotonic() if now is None else now
    with _rating_lock:
        active_since = _rating_tasks.get(session_id)
        if active_since is not None and started_at - active_since < RATING_TASK_STALE_SECONDS:
            return None
        _rating_tasks[session_id] = started_at
    return started_at, active_since is not None


def _release_rating_task(session_id: int, task_token: float) -> None:
    """只允许当前登记的任务释放状态，避免旧线程误删新恢复任务。"""
    with _rating_lock:
        if _rating_tasks.get(session_id) == task_token:
            _rating_tasks.pop(session_id, None)


def _to_ms(dt) -> int:
    """存储为 naive UTC，必须先标成 UTC 再转毫秒，否则差出时区偏移（东八区 8 小时）。"""
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def _clamp(value, lo, hi) -> int:
    """大模型返回的分值可能是字符串/越界，统一转 int 并夹到范围内"""
    try:
        v = int(value)
    except (TypeError, ValueError):
        v = lo
    return max(lo, min(hi, v))


def _build_transcript(messages) -> list:
    """对话记录（含教练干预），病历只交付最终保存版本。"""
    latest_record_id = next(
        (
            m.id for m in reversed(messages)
            if m.role == "user" and m.extra and m.extra.get("kind") == "medical_record"
        ),
        None,
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "kind": m.extra.get("kind") if m.extra else None,
            "voice_assessments": (m.extra or {}).get('voice_assessments', []),
        }
        for m in messages
        if not (m.role == "ai" and m.extra and m.extra.get("superseded"))
        and not (
            m.role == "user" and m.extra and m.extra.get("kind") == "medical_record"
            and m.id != latest_record_id
        )
    ]


def _has_action(text: str, keyword: str) -> bool:
    """粗略排除“不能/不要/禁止做某事”的否定提及。"""
    if keyword not in text:
        return False
    return not any(negative + keyword in text for negative in ("不能", "不要", "禁止", "不应", "不可以"))


def _sample_completeness(user_text: str) -> dict:
    symptom_clues = sum(
        any(word in user_text for word in group)
        for group in (
            ("发烧", "发热", "头痛", "腹痛", "咳嗽", "红疹", "疼"),
            ("天", "小时", "昨晚", "今天", "开始"),
            ("度", "严重", "轻微", "剧烈", "最高"),
            ("伴有", "还有", "同时", "没有", "无"),
        )
    )
    return {
        "symptoms": min(100, symptom_clues * 25),
        "allergies": 100 if any(word in user_text for word in ("过敏", "青霉素")) else 0,
        "medications": 100 if any(word in user_text for word in ("用药", "吃药", "服用", "没在吃药", "保健品")) else 0,
        "history": 100 if any(word in user_text for word in ("病史", "既往", "高血压", "哮喘", "手术")) else 0,
        "events": 100 if any(word in user_text for word in ("开始", "后来", "加重", "缓解", "昨晚", "今早")) else 0,
    }


def _fallback_rating(scene_type: str, messages) -> dict:
    """大模型评分不可用时按明确规则给出可解释的保底评分。"""
    all_user_messages = [(index, message) for index, message in enumerate(messages) if message.role == "user"]
    record_messages = [
        (index, message)
        for index, message in all_user_messages
        if getattr(message, "extra", None) and message.extra.get("kind") == "medical_record"
    ]
    user_messages = [
        (index, message.content)
        for index, message in all_user_messages
        if not (getattr(message, "extra", None) and message.extra.get("kind") in ("medical_record", "coach_q"))
    ]
    user_text = " ".join(content for _, content in user_messages)
    record_text = record_messages[-1][1].content if record_messages else ""
    ai_text = " ".join(message.content for message in messages if message.role == "ai")
    system_text = " ".join(message.content for message in messages if message.role == "system")
    all_text = " ".join((system_text, user_text, ai_text))
    highlights = []
    mistakes = []
    annotations = []
    osce_checklist = None
    medical_record_review = None

    if scene_type == "choking":
        recognized = any(word in user_text for word in ("完全梗阻", "不能说话", "不能咳嗽", "噎住"))
        assessed = any(word in user_text for word in ("能说话", "能咳嗽", "能呼吸", "噎住了吗"))
        called = "120" in user_text or "呼救" in user_text
        back_blows = "拍背" in user_text or "背部拍击" in user_text
        thrust = "海姆立克" in user_text or "腹部冲击" in user_text
        technique = sum(word in user_text for word in ("身后", "肚脐", "肋弓", "向内", "向上", "5次"))
        aftercare = any(word in user_text for word in ("就医", "医院检查", "并发症", "哪里疼"))
        harmful = any(_has_action(user_text, word) for word in ("喝水", "平躺", "抠喉"))

        accuracy = (10 if recognized else 0) + (10 if not harmful else 0) + min(15, (5 if back_blows else 0) + (5 if thrust else 0) + technique) + (5 if aftercare else 0)
        warmth = (10 if any(word in user_text for word in ("别害怕", "不要怕", "没事", "我在")) else 0) + (10 if technique >= 2 else 4 if thrust or back_blows else 0) + (10 if any(word in user_text for word in ("感觉", "观察", "哪里疼", "还好吗")) else 0)
        decision = (10 if assessed or recognized else 0) + (10 if called and (back_blows or thrust) else 5 if called or back_blows or thrust else 0) + (10 if aftercare else 0)
        if recognized: highlights.append("识别了完全梗阻的关键表现")
        else: mistakes.append("未明确判断患者是否为完全梗阻")
        if back_blows and thrust: highlights.append("提到了拍背与腹部冲击的递进流程")
        else: mistakes.append("急救动作流程还不完整")
        if harmful: mistakes.append("出现可能加重梗阻的危险操作")
        if not aftercare: mistakes.append("异物排出后仍应建议医务人员评估")
        optimal = ["评估", "判断梗阻", "呼救120", "拍背5次", "腹部冲击", "循环检查", "后续就医"]
        user_path = [name for ok, name in ((assessed, "评估"), (recognized, "判断梗阻"), (called, "呼救120"), (back_blows, "拍背"), (thrust, "腹部冲击"), (aftercare, "后续就医")) if ok]
    elif scene_type == "osce":
        hpi_groups = (
            ("哪里不舒服", "主要不适", "怎么了", "主诉"),
            ("多久", "什么时候", "起病", "开始"),
            ("部位", "性质", "程度"),
            ("诱因", "加重", "缓解", "活动后"),
            ("伴随", "还有", "有没有"),
            ("治疗", "检查过", "吃过药", "诊治"),
            ("精神", "睡眠", "食欲", "大小便", "体重", "体力"),
        )
        hpi_count = sum(any(word in user_text for word in group) for group in hpi_groups)
        other_terms = ("既往", "过敏", "手术", "外伤", "输血", "用药", "个人史", "月经", "婚育", "家族")
        other_count = sum(word in user_text for word in other_terms)
        exam_requested = any(word in user_text for word in ("生命体征", "查体", "体格检查", "听诊", "心电图", "超声", "胸片", "血常规"))

        accuracy = min(28, round(hpi_count / len(hpi_groups) * 28)) + min(10, other_count * 2) + (2 if exam_requested else 0)
        opening_points = sum(
            any(word in user_text for word in group)
            for group in (("您好", "你好"), ("我是", "医生"), ("姓名", "名字", "身份"), ("同意", "配合", "方便"))
        )
        communication_points = sum(
            any(word in user_text for word in group)
            for group in (("请您", "请问", "麻烦"), ("理解", "别担心", "慢慢说", "辛苦"))
        )
        warmth = min(10, opening_points * 3) + min(10, communication_points * 5)

        required_sections = ("基本信息", "主诉", "现病史", "其他病史", "体格检查", "辅助检查", "病历摘要", "初步诊断")
        section_count = sum(section in record_text for section in required_sections)
        record_points = min(20, round(section_count / len(required_sections) * 20)) if record_text else 0
        reasoning_points = min(10, (4 if hpi_count >= 5 else hpi_count) + (3 if other_count >= 3 else other_count) + (2 if exam_requested else 0))
        diagnosis_points = 0
        if record_text and "初步诊断" in record_text:
            diagnosis_points = 5
            if any(word in record_text for word in ("风湿性心脏病", "二尖瓣", "心房颤动", "心功能不全", "鉴别")):
                diagnosis_points = 10
        decision = reasoning_points + record_points + diagnosis_points

        if hpi_count >= 5:
            highlights.append("现病史追问围绕主诉展开，覆盖了多数关键要素")
        else:
            mistakes.append("现病史应补充起病、演变、伴随症状、诊治经过和一般情况")
        if other_count >= 4:
            highlights.append("其他病史采集较完整")
        else:
            mistakes.append("既往史、过敏史、个人婚育史或家族史仍有遗漏")
        if not record_text:
            mistakes.append("未提交学生独立书写的病历记录")
        elif section_count >= 6:
            highlights.append("病历记录结构较完整")
        else:
            mistakes.append("病历记录需补齐规范结构并区分主观病史与客观结果")
        if not exam_requested:
            mistakes.append("问诊结束后应提出至少一项针对性检查")

        optimal = ["接诊准备", "开放问诊", "现病史", "其他病史", "快速检查", "病历书写", "初步诊断"]
        user_path = [
            name for ok, name in (
                (opening_points >= 2, "接诊准备"), (hpi_count > 0, "开放问诊"),
                (hpi_count >= 4, "现病史"), (other_count >= 3, "其他病史"),
                (exam_requested, "快速检查"), (bool(record_text), "病历书写"),
                (diagnosis_points > 0, "初步诊断"),
            ) if ok
        ]
        osce_checklist = {
            "opening_communication": min(100, opening_points * 25),
            "chief_complaint_hpi": min(100, round(hpi_count / len(hpi_groups) * 100)),
            "other_history": min(100, other_count * 10),
            "exam_investigations": 100 if exam_requested else 0,
            "medical_record": min(100, round(section_count / len(required_sections) * 100)) if record_text else 0,
        }
        medical_record_review = (
            "已提交病历；请重点核对时间顺序、重要阳性与鉴别意义阴性信息，并避免补写问诊中未获得的资料。"
            if record_text
            else "未提交病历记录，因此病历书写项不得分。"
        )
    else:
        registration = any(word in user_text for word in ("挂号", "预约", "窗口", "自助机", "智能导诊", "急诊"))
        department = "科" in user_text or "门诊" in user_text
        printed_report = "报到单" in user_text and any(word in user_text for word in ("自助机", "打印", "初诊"))
        clinic_scan = "报到机" in user_text and any(word in user_text for word in ("诊间", "扫码", "扫描", "报到"))
        sample = _sample_completeness(user_text)
        medication = sum(any(word in user_text for word in group) for group in (("怎么吃", "用法", "用量"), ("副作用", "不良反应"), ("冲突", "一起吃"), ("复诊", "再来", "加重")))
        polite = sum(user_text.count(word) for word in ("您好", "请问", "谢谢", "麻烦"))
        insurance = any(word in user_text for word in ("医保", "费用", "报销", "多少钱"))
        manual_window = any(word in user_text for word in ("人工收费窗口", "人工缴费窗口", "人工窗口", "收费窗口"))
        paid = any(word in user_text for word in ("缴费", "付费", "支付", "医保", "自费"))
        emergency_case = any(
            word in all_text
            for word in ("急危重症", "脑出血", "脑卒中", "意识障碍", "严重呼吸困难", "大出血", "休克", "生命危险", "绿色通道", "从未有过的剧烈头痛")
        )
        emergency_priority = any(
            word in user_text
            for word in ("急诊", "120", "绿色通道", "立即检查", "紧急检查", "先救治", "先抢救", "立即手术", "先治疗")
        )
        proactive = any(score > 0 for score in (sample["allergies"], sample["medications"], sample["history"]))

        accuracy = (10 if registration and department else 6 if registration else 0) + min(10, round(sum(sample.values()) / 50)) + min(10, medication * 3)
        warmth = min(10, polite * 3) + (15 if proactive else 7 if sample["symptoms"] >= 50 else 0) + (15 if sample["symptoms"] >= 75 else 8 if sample["symptoms"] >= 50 else 0)
        if emergency_case:
            decision = (
                (15 if emergency_priority else 5)
                + (5 if sample["symptoms"] >= 50 else 0)
                + (5 if any(word in user_text for word in ("加重", "意识", "呕吐", "呼吸")) else 0)
                + (5 if any(word in user_text for word in ("陪同", "联系家属", "听从安排", "配合")) else 0)
            )
        else:
            decision = (
                (5 if registration else 0)
                + (5 if printed_report and clinic_scan else 0)
                + (10 if manual_window and paid else 4 if insurance else 0)
                + (5 if any(word in user_text for word in ("复诊", "再来", "加重")) else 0)
                + (5 if any(word in user_text for word in ("注意", "预防", "休息", "饮食")) else 0)
            )
        if registration: highlights.append("主动选择或询问了挂号方式")
        else: mistakes.append("尚未完成挂号方式选择")
        if emergency_case:
            if emergency_priority:
                highlights.append("急危重症时优先急诊检查和救治，没有被报到或缴费延误")
            else:
                mistakes.append("疑似急危重症时应立即进入急诊检查和救治")
        elif printed_report and clinic_scan:
            highlights.append("完整完成了打印报到单和诊间扫码报到")
        else:
            mistakes.append("初诊挂号后应先打印报到单，再到诊间报到机扫码")
        if sample["symptoms"] >= 75: highlights.append("症状描述包含时间、程度和伴随表现")
        else: mistakes.append("症状描述可补充时间、程度和伴随症状")
        if medication >= 2:
            highlights.append("关注了用药安全和注意事项")
        elif not emergency_case:
            mistakes.append("需要主动确认用法、副作用和复诊指征")
        if not emergency_case and manual_window and paid:
            highlights.append("在取药或检查治疗前完成了人工窗口缴费")
        elif not emergency_case:
            mistakes.append("医嘱开具后应先到人工收费窗口缴费")
        if emergency_case:
            optimal = ["急诊分诊", "关键表达", "绿色通道", "紧急检查", "抢救治疗", "稳定后结算"]
            user_path = [name for ok, name in ((registration, "急诊分诊"), (sample["symptoms"] >= 50, "描述症状"), (emergency_priority, "优先救治")) if ok]
        else:
            optimal = ["选择挂号", "正确选科", "打印报到单", "诊间扫码", "完整描述", "诊断医嘱", "人工缴费", "取药执行"]
            user_path = [name for ok, name in ((registration, "选择挂号"), (department, "选择科室"), (printed_report, "打印报到单"), (clinic_scan, "诊间扫码"), (sample["symptoms"] >= 50, "描述症状"), (medication > 0, "询问用药"), (manual_window and paid, "人工缴费")) if ok]

    for index, content in user_messages:
        if scene_type == "choking" and any(word in content for word in ("能说话", "能咳嗽", "拍背", "海姆立克")):
            annotations.append({"message_index": index, "good_points": "包含关键评估或急救动作"})
        if scene_type == "first_visit" and any(word in content for word in ("您好", "请问", "过敏", "怎么吃", "医保", "报到单", "报到机", "人工窗口")):
            annotations.append({"message_index": index, "good_points": "体现主动、礼貌的就医沟通"})
        if scene_type == "osce" and any(word in content for word in ("哪里不舒服", "多久", "既往", "过敏", "家族", "月经")):
            annotations.append({"message_index": index, "good_points": "问诊覆盖了关键病史要素"})
    if scene_type == "osce" and record_messages:
        annotations.append({"message_index": record_messages[-1][0], "good_points": "已提交独立病历记录"})

    accuracy = max(0, accuracy - (20 if scene_type == "choking" and harmful else 0))
    dimensions = {"accuracy": accuracy, "warmth": warmth, "decision": decision}
    return {
        "dimensions": dimensions,
        "total_score": sum(dimensions.values()),
        "summary": "本次为规则引擎评分。你已经完成了部分关键训练步骤；请结合下方路径对比，补齐遗漏环节后再次练习。",
        "highlights": highlights[:4],
        "key_mistakes": mistakes[:4],
        "decision_tree": {
            "user_path": user_path or ["开始训练"],
            "optimal_path": optimal,
            "gaps": "；".join(mistakes[:3]) or "关键流程较完整。",
        },
        "message_annotations": annotations[:10],
        "sample_completeness": _sample_completeness(user_text) if scene_type == "first_visit" else None,
        "osce_checklist": osce_checklist,
        "medical_record_review": medical_record_review,
        "rating_source": "rules",
    }


def _recent_training_history(db: Session, user_id: int, exclude_session_id: int, limit: int = 5) -> list[dict]:
    """该学生之前 limit 次已评分训练的摘要（分数 + 实际步骤），供复盘智能体对比进步。"""
    rows = (
        db.query(Result, ChatSession)
        .join(ChatSession, ChatSession.id == Result.session_id)
        .filter(Result.user_id == user_id, Result.session_id != exclude_session_id)
        .order_by(Result.session_id.desc())
        .limit(limit)
        .all()
    )
    history = []
    scene_titles = {
        s.id: s.title
        for s in db.query(Scene).filter(
            Scene.id.in_({session_row.scene_id for _, session_row in rows})
        ).all()
    }
    for result_row, session_row in reversed(rows):  # 按时间正序展示
        details = result_row.details or {}
        steps = ((details.get("decision_tree") or {}).get("user_path")) or []
        history.append({
            "scene": scene_titles.get(session_row.scene_id, f"场景{session_row.scene_id}"),
            "score": result_row.total_score,
            "steps": steps,
        })
    return history


def _generate_rating(
    db: Session,
    session: ChatSession,
    scene: Scene,
    messages,
    use_agent: bool = True,
) -> dict:
    """调用评分智能体生成评分，并落库（results 表）"""
    scene_type = get_scene_type(scene)
    scorer_prompt = build_scorer_system_prompt(scene, scene_type)

    transcript = _build_transcript(messages)
    history = _recent_training_history(db, session.user_id, session.id)
    history_text = (
        "\n\n该学生最近5次训练历史（分数 + 实际步骤，可与本次表现对比）：\n"
        + "\n".join(
            f"- 第{i}次（场景{item['scene']}）：{item['score']}分，步骤：{' → '.join(item['steps']) or '（无记录）'}"
            for i, item in enumerate(history, 1)
        )
        + "\n可在 summary 中适当结合历史表现点评进步或退步，但评分只依据本次对话。"
        if history
        else ""
    )
    user_content = (
        "请对以下对话记录评分。对话中 role=user 是受训学生的发言，"
        "role=ai 是角色扮演（患者/医生），role=coach 是教练的干预。\n"
        "对话记录：\n" + "\n".join(
            f"[{i}] {m['role']}"
            + (f" (kind={m['kind']})" if m.get("kind") else "")
            + ': ' + with_voice(m['content'], m.get('voice_assessments'))
            for i, m in enumerate(transcript)
        )
        + history_text
    )

    if use_agent:
        try:
            rating = llm.call_llm_json(
                [{"role": "user", "content": user_content}],
                scorer_prompt,
                timeout_seconds=RATING_REQUEST_TIMEOUT_SECONDS,
                max_retries=0,
            )
            rating["rating_source"] = "agent"
        except Exception as error:
            logger.warning(
                "评分智能体不可用，改用规则保底评分 session_id=%s error=%s",
                session.id,
                type(error).__name__,
            )
            rating = _fallback_rating(scene_type, messages)
    else:
        logger.warning(
            "评分任务超过 %.0f 秒，改用规则保底评分 session_id=%s",
            RATING_TASK_STALE_SECONDS,
            session.id,
        )
        rating = _fallback_rating(scene_type, messages)

    # 分值校验：各维度按场景满分封顶
    dim_max = {
        "choking": (40, 30, 30),
        "first_visit": (30, 40, 30),
        "osce": (40, 20, 40),
        "generic": (40, 30, 30),
    }[scene_type]
    dims = rating.get("dimensions") or {}
    accuracy = _clamp(dims.get("accuracy"), 0, dim_max[0])
    warmth = _clamp(dims.get("warmth"), 0, dim_max[1])
    decision = _clamp(dims.get("decision"), 0, dim_max[2])

    # 落库前再次检查，防止陈旧任务恢复时两个线程重复写同一会话。
    existing = db.query(Result).filter(Result.session_id == session.id).first()
    if existing:
        if not session.is_rated:
            session.is_rated = 1
            db.commit()
        return existing.details or rating

    result = Result(
        session_id=session.id,
        user_id=session.user_id,
        total_score=accuracy + warmth + decision,
        accuracy=accuracy,
        warmth=warmth,
        decision=decision,
        details=rating,
    )
    session.is_rated = 1
    db.add(result)
    try:
        db.commit()
    except IntegrityError:
        # results.session_id 有唯一索引；极端竞态下保留先完成的评分即可。
        db.rollback()
        existing = db.query(Result).filter(Result.session_id == session.id).first()
        if existing:
            return existing.details or rating
        raise

    return rating


def _run_rating_task(session_id: int, task_token: float, force_fallback: bool = False):
    """在后台线程中生成评分（独立数据库会话，不跨线程共用请求级 Session）"""
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return
        if db.query(Result).filter(Result.session_id == session_id).first():
            return
        scene = db.query(Scene).filter(Scene.id == session.scene_id).first()
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )
        if scene:
            _generate_rating(db, session, scene, messages, use_agent=not force_fallback)
    except Exception:
        logger.exception("后台评分任务失败 session_id=%s", session_id)
    finally:
        db.close()
        _release_rating_task(session_id, task_token)


@router.get("/{session_id}")
async def get_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取评分结果

    逻辑：
    1. 校验会话归属
    2. 已有评分 → 直接返回缓存（results 表），status=ready
    3. 没有评分 → 启动后台线程生成，立即返回 status=pending，前端轮询直到 ready
    4. 组装：总分 + 三维度 + 对话回放（带 issue_points/good_points 标注）+ 决策树
    """
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # 容错：直接访问评分页但没调过 /chat/end 的，视为已结束
    if not session.ended_at:
        session.ended_at = datetime.utcnow()
        db.commit()

    scene = db.query(Scene).filter(Scene.id == session.scene_id).first()
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    # 已评分 → 读缓存；未评分 → 后台线程生成（有兜底规则评分，最终一定会落库）
    result = db.query(Result).filter(Result.session_id == session.id).first()

    if not result:
        task_claim = _claim_rating_task(session.id)
        if task_claim is not None:
            task_token, recovered_stale_task = task_claim
            try:
                threading.Thread(
                    target=_run_rating_task,
                    args=(session.id, task_token, recovered_stale_task),
                    daemon=True,
                ).start()
            except Exception:
                _release_rating_task(session.id, task_token)
                logger.exception("无法启动后台评分任务 session_id=%s", session.id)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="评分任务暂时无法启动，请稍后重试",
                )
        # 立即返回，让前端轮询——不要让 HTTP 请求扛着整个评分过程（容易超时）
        return {"status": "pending", "session_id": session.id}

    rating = result.details or {}
    accuracy, warmth, decision = result.accuracy, result.warmth, result.decision

    # 对话回放：套用评分智能体的消息标注（message_index 对应消息列表序号）
    annotations = {a.get("message_index"): a for a in (rating.get("message_annotations") or [])}
    replay = []
    for i, m in enumerate(messages):
        ann = annotations.get(i) or {}
        replay.append({
            "id": m.id,
            "role": m.role,
            "kind": m.extra.get("kind") if m.extra else None,
            "content": m.content,
            "timestamp": _to_ms(m.timestamp) if m.timestamp else None,
            "issue_points": ann.get("issue_points"),
            "good_points": ann.get("good_points"),
            "voice_assessments": (m.extra or {}).get('voice_assessments', []),
        })

    scene_type = get_scene_type(scene)
    dimension_max = {
        "choking": {"accuracy": 40, "warmth": 30, "decision": 30},
        "first_visit": {"accuracy": 30, "warmth": 40, "decision": 30},
        "osce": {"accuracy": 40, "warmth": 20, "decision": 40},
        "generic": {"accuracy": 40, "warmth": 30, "decision": 30},
    }[scene_type]
    user_text = " ".join(m.content for m in messages if m.role == "user")
    communication_words = Counter(
        word for word in ("您好", "请问", "谢谢", "麻烦", "多久", "怎么")
        for _ in range(user_text.count(word))
    )

    return {
        "status": "ready",
        "session_id": session.id,
        "scene_id": scene.id,
        "scene_title": scene.title,
        "scene_type": scene_type,
        "total_score": accuracy + warmth + decision,
        "dimensions": {"accuracy": accuracy, "warmth": warmth, "decision": decision},
        "dimension_max": dimension_max,
        "messages": replay,
        "decision_tree": rating.get("decision_tree"),
        "summary": rating.get("summary"),
        "highlights": rating.get("highlights"),
        "key_mistakes": rating.get("key_mistakes"),
        "sample_completeness": rating.get("sample_completeness") or (
            _sample_completeness(user_text) if scene_type == "first_visit" else None
        ),
        "osce_checklist": rating.get("osce_checklist"),
        "medical_record_review": rating.get("medical_record_review"),
        "communication_words": [
            {"word": word, "count": count}
            for word, count in communication_words.most_common()
        ],
        "rating_source": rating.get("rating_source", "agent"),
        "share_url": f"/result/{session.id}",
    }


@router.post("/{session_id}/share")
async def share_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成站内成绩链接；公开分享由前端 Web Share/剪贴板能力完成。"""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return {"share_url": f"/result/{session.id}"}
