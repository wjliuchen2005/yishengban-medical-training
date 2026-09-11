"""动态训练情景生成。

急救体征和首次 OSCE 病例来自已审核池。首次 OSCE 只改变非医学性开场细节；
第二次起由场景生成智能体产生新病例并经过结构校验。模型不可用时使用本地备用病例，保证训练可开始。
"""
from __future__ import annotations

import json
import logging
import secrets
from typing import Any

from app.ai import llm

logger = logging.getLogger(__name__)
_random = secrets.SystemRandom()


FIRST_VISIT_CASES = (
    {
        "scenario_id": "S00",
        "gender": "any",
        "symptoms": "咽部不适、轻微流鼻涕和咳嗽已经2天，没有高热或呼吸困难",
        "departments": ["校医院", "全科医学科", "普通内科"],
        "difficulty": 1,
        "case_group": "intro",
    },
    {
        "scenario_id": "S01",
        "gender": "any",
        "symptoms": "发热2天，最高体温38.5℃，伴有头痛",
        "departments": ["发热门诊", "内科"],
        "difficulty": 1,
        "case_group": "special",
    },
    {
        "scenario_id": "S02",
        "gender": "any",
        "symptoms": "从昨晚开始腹痛、腹泻，今天症状仍未缓解",
        "departments": ["消化内科", "急诊科"],
        "difficulty": 2,
        "case_group": "common",
    },
    {
        "scenario_id": "S03",
        "gender": "any",
        "symptoms": "近两天反复胸闷、心慌，活动后更加明显",
        "departments": ["心内科", "急诊科"],
        "difficulty": 3,
        "case_group": "special",
    },
    {
        "scenario_id": "S04",
        "gender": "any",
        "symptoms": "手臂和颈部出现瘙痒红疹，已经持续3天",
        "departments": ["皮肤科"],
        "difficulty": 1,
        "case_group": "common",
    },
    {
        "scenario_id": "S05",
        "gender": "female",
        "symptoms": "月经周期连续几个月不规律，并伴有下腹不适",
        "departments": ["妇科"],
        "difficulty": 2,
        "case_group": "special",
    },
    {
        "scenario_id": "S06",
        "gender": "any",
        "symptoms": "运动后右膝疼痛，上下楼时更加明显",
        "departments": ["骨科", "运动医学科"],
        "difficulty": 2,
        "case_group": "common",
    },
    {
        "scenario_id": "S07",
        "gender": "any",
        "symptoms": "咳嗽已经2周，今天发现痰中带有少量血丝",
        "departments": ["呼吸内科", "胸外科"],
        "difficulty": 3,
        "case_group": "special",
    },
    {
        "scenario_id": "S08",
        "gender": "any",
        "symptoms": "突然出现从未有过的剧烈头痛，并伴有呕吐和视物模糊",
        "departments": ["急诊科", "神经内科"],
        "difficulty": 4,
        "case_group": "special",
        "urgent": True,
    },
    {
        "scenario_id": "S09",
        "gender": "female",
        "symptoms": "月经推迟，验孕结果不明确，想去医院进一步确认",
        "departments": ["妇科", "计划生育科"],
        "difficulty": 3,
        "case_group": "special",
    },
    {
        "scenario_id": "S10",
        "gender": "any",
        "symptoms": "这两天尿频、尿急，排尿时有明显刺痛",
        "departments": ["泌尿外科", "肾内科"],
        "difficulty": 2,
        "case_group": "common",
    },
)

FIRST_VISIT_SETTINGS = (
    "周一上午，你在上完第一节课后",
    "周末留校期间，你在宿舍休息时",
    "一次社团活动结束后，你回到宿舍",
    "连续几天课程排得很满，今天早上",
    "刚结束体育课，你坐在操场边休息时",
)

FIRST_VISIT_NAMES = {
    "male": ("陈宇", "周睿", "王晨", "李明轩"),
    "female": ("林悦", "张雨桐", "陈思妍", "王欣怡"),
    "unspecified": ("陈宇", "林悦", "周睿", "张雨桐"),
}

FIRST_VISIT_VOICE_CAST_FALLBACK = {
    "narrator": {"voice": "苏打", "gender": "male"},
    "registrar": {"voice": "茉莉", "gender": "female"},
    "doctor": {"voice": "白桦", "gender": "male"},
    "cashier": {"voice": "冰糖", "gender": "female"},
    "pharmacist": {"voice": "茉莉", "gender": "female"},
}

# MiMo 内置声线的展示性别由声线本身决定，不能信任模型自由填写的 gender，
# 否则会出现界面标“男”但实际播放女声的割裂。
MIMO_VOICE_GENDER = {
    "冰糖": "female",
    "茉莉": "female",
    "白桦": "male",
    "苏打": "male",
}

CHOKING_CHARACTERS = ("室友", "同学", "食堂阿姨", "路人", "年轻女生", "中年男性")
CHOKING_LOCATIONS = ("食堂", "宿舍", "图书馆咖啡区", "街边小吃店", "操场边")
CHOKING_OBJECTS = ("肉块", "果冻", "坚果", "年糕", "鱼丸")

# 特殊患者（多次训练后随机出现）：腹部冲击不可用，考察胸部冲击
CHOKING_SPECIAL_CASES = (
    {
        "character": "怀孕八个多月的女老师",
        "note": "患者是孕晚期孕妇，腹部冲击不可用。正确做法是5次拍背+5次胸部冲击"
                "（拳置于两乳连线中点胸骨中段，向后冲击）。如果用户执行腹部冲击，"
                "要表现出明显不适并捂住腹部皱眉（动作不适用）。",
    },
    {
        "character": "体型肥胖的食堂师傅",
        "note": "患者体型肥胖，施救者无法环抱其腹部，腹部冲击不可行。正确做法是"
                "5次拍背+5次胸部冲击（拳置于两乳连线中点胸骨中段，向后冲击）。"
                "如果用户强行执行腹部冲击，要表现出够不到、动作无效（动作不适用）。",
    },
)


def _choose_without_recent(options: list[Any], recent_values: set[Any], key=None) -> Any:
    identify = key or (lambda item: item)
    fresh = [item for item in options if identify(item) not in recent_values]
    return _random.choice(fresh or options)


def _refine_narrative(base_description: str, immutable_fact: str, scene_type: str) -> tuple[str, str]:
    """让场景生成智能体润色非医学细节，返回文案和来源标记。"""
    extra_rule = (
        "5. 场景是异物梗阻时：不得直接说明患者被什么东西噎住（用户无法得知），"
        "异物只能作为环境线索（如桌上没吃完的食物包装）出现。"
        if scene_type == "异物梗阻急救"
        else ""
    )
    prompt = f"""你是医疗沟通训练系统的场景生成智能体。

请把下面的基础情境改写成自然、有画面感的第二人称开场。你只能微调时间、环境和就医动机，不得新增诊断、不得替用户做决定、不得改变核心事实。

场景类型：{scene_type}
必须逐字保留的核心事实：{immutable_fact}
基础情境：{base_description}

要求：
1. 80-140个汉字；
2. 只描述发生了什么，不扮演患者、医生或挂号员说话；
3. 不透露正确科室或标准答案；
4. 返回合法 JSON：{{"description": "改写后的情境"}}。
{extra_rule}
"""
    try:
        payload = llm.call_llm_json([], prompt, llm.CHAT_REASONING_EFFORT)
        description = str(payload.get("description") or "").strip()
        if 40 <= len(description) <= 220 and immutable_fact in description:
            return description, "agent"
    except Exception as exc:  # 场景生成是增强链路，不能阻断训练开始
        logger.info("场景生成智能体不可用，使用本地情景模板：%s", exc)
    return base_description, "template"


def _cast_display_name(role: str, value=None) -> str:
    defaults = {"narrator": "就医引导", "registrar": "挂号员·林悦", "doctor": "医生·陈宁", "cashier": "收费员·周晴", "pharmacist": "药师·许安"}
    name = str(value or "").strip()
    return name if 2 <= len(name) <= 20 and "角色" not in name and "·" in name else defaults[role]


def _generate_first_visit_voice_cast() -> tuple[dict[str, dict[str, str]], str]:
    """Let the scene agent choose a per-session cast with an exclusive doctor voice."""
    prompt = """你是场景生成智能体，请为第一次独立看病中的角色分配 MiMo 中文声线。
可选声线只有：冰糖、茉莉、白桦、苏打。每次训练可重新选择医生声线；但在同一次训练中，医生声线不得被旁白、挂号员、收费员或药师使用。非医生角色之间可以复用声线。
同时为工作人员生成自然的中文姓名，在每项增加 display_name（如挂号员·林悦、医生·陈宁、收费员·周晴、药师·许安）；旁白命名为就医引导。姓名和身份在本次训练中保持一致。
只返回合法 JSON：
{"voice_cast":{"narrator":{"voice":"苏打","gender":"male"},"registrar":{"voice":"茉莉","gender":"female"},"doctor":{"voice":"白桦","gender":"male"},"cashier":{"voice":"冰糖","gender":"female"},"pharmacist":{"voice":"茉莉","gender":"female"}}}
"""
    try:
        payload = llm.call_llm_json([], prompt, llm.CHAT_REASONING_EFFORT)
        raw = payload.get("voice_cast") if isinstance(payload, dict) else None
        if not isinstance(raw, dict):
            raise ValueError("voice_cast missing")
        cast: dict[str, dict[str, str]] = {}
        for role, fallback in FIRST_VISIT_VOICE_CAST_FALLBACK.items():
            item = raw.get(role)
            if not isinstance(item, dict):
                raise ValueError(f"invalid role {role}")
            voice = str(item.get("voice") or "")
            if voice not in MIMO_VOICE_GENDER:
                raise ValueError(f"invalid voice for {role}")
            cast[role] = {"voice": voice, "gender": MIMO_VOICE_GENDER[voice], "display_name": _cast_display_name(role, item.get("display_name"))}
        if any(item["voice"] == cast["doctor"]["voice"] for role, item in cast.items() if role != "doctor"):
            raise ValueError("doctor voice must be exclusive inside a session")
        return cast, "agent"
    except Exception as exc:
        logger.info("声线编排智能体不可用，使用安全默认声线：%s", exc)
        voices = list(MIMO_VOICE_GENDER)
        doctor_voice = _random.choice(voices)
        other_voices = [voice for voice in voices if voice != doctor_voice]
        cast = {}
        for role in FIRST_VISIT_VOICE_CAST_FALLBACK:
            voice = doctor_voice if role == "doctor" else _random.choice(other_voices)
            cast[role] = {"voice": voice, "gender": MIMO_VOICE_GENDER[voice], "display_name": _cast_display_name(role)}
        return cast, "template"


def _first_visit_context(gender: str, previous_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        case for case in FIRST_VISIT_CASES
        if case["gender"] == "any" or case["gender"] == gender
    ]
    # 首练固定为高频、低复杂度的感冒样问题；第2-3次仍使用常见问题。
    # 从第4次起引入头痛、胸闷等特殊情况。若最近三次都是常见问题，
    # 则下一次强制补入特殊病例，避免只随机到简单病例。
    if not previous_contexts:
        curriculum_pool = [case for case in eligible if case["case_group"] == "intro"]
        training_round = 1
    elif len(previous_contexts) < 3:
        curriculum_pool = [case for case in eligible if case["case_group"] == "common"]
        training_round = len(previous_contexts) + 1
    elif not any(item.get("case_group") == "special" for item in previous_contexts[-3:]):
        curriculum_pool = [case for case in eligible if case["case_group"] == "special"]
        training_round = 4
    else:
        curriculum_pool = [case for case in eligible if case["case_group"] != "intro"]
        training_round = 4

    recent_ids = {item.get("scenario_id") for item in previous_contexts[-3:]}
    case = _choose_without_recent(curriculum_pool, recent_ids, key=lambda item: item["scenario_id"])
    recent_settings = {item.get("setting") for item in previous_contexts[-2:]}
    setting = _choose_without_recent(list(FIRST_VISIT_SETTINGS), recent_settings)
    recent_names = {item.get("patient_name") for item in previous_contexts[-2:]}
    patient_name = _choose_without_recent(
        list(FIRST_VISIT_NAMES.get(gender, FIRST_VISIT_NAMES["unspecified"])),
        recent_names,
    )
    primary_department = case["departments"][0]
    call_notice = f"请{patient_name}，{patient_name}到{primary_department}3诊室就诊。"

    base_description = (
        f"{setting}，你发现自己{case['symptoms']}。本次模拟就诊姓名为{patient_name}。你第一次需要独自处理就医流程，"
        "身边暂时没有家人或同学陪同。"
    )
    narrative, source = _refine_narrative(
        base_description,
        case["symptoms"],
        "第一次独立看病",
    )
    voice_cast, voice_cast_source = _generate_first_visit_voice_cast()

    if case.get("urgent"):
        first_step = "判断紧急程度并前往急诊分诊"
        actions = [
            {"label": "直接前往急诊", "value": "症状突然且很严重，我选择直接前往急诊分诊。"},
            {"label": "请分诊台评估", "value": "我先向分诊台说明症状，请护士帮我判断紧急程度。"},
        ]
        guidance = (
            "这些症状可能属于急症。你的第一步是尽快到急诊分诊，并清楚说明症状；"
            "急症处置不应被普通门诊的报到流程延误。"
        )
    else:
        first_step = "选择挂号方式"
        actions = [
            {
                "label": "线上预约挂号",
                "value": "我选择线上预约挂号。",
            },
            {
                "label": "线下现场挂号",
                "value": "我选择到医院线下现场挂号。",
            },
            {
                "label": "省人医微信公众号智能分诊",
                "value": "我不确定该挂哪个科，先打开省人医微信公众号使用智能分诊。",
            },
        ]
        guidance = (
            "你的第一步是选择挂号方式和科室：可以线上预约或线下挂号；"
            "如果不确定科室，可以在【省人医微信公众号】先使用智能分诊相关功能。"
        )

    return {
        "opening_message": f"{narrative}\n\n{guidance}请告诉我你准备怎么做。",
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "scenario_id": case["scenario_id"],
            "patient_name": patient_name,
            "first_step": first_step,
            "quick_actions": actions,
            "voice_cast": voice_cast,
        },
        "context": {
            "scene_type": "first_visit",
            "scenario_id": case["scenario_id"],
            "patient_name": patient_name,
            "call_notice": call_notice,
            "outpatient_hours": {"morning": "08:00-11:30", "afternoon": "14:00-17:30"},
            "training_round": training_round,
            "case_group": case["case_group"],
            "gender": gender,
            "symptoms": case["symptoms"],
            "correct_departments": case["departments"],
            "difficulty": case["difficulty"],
            "urgent": bool(case.get("urgent")),
            "setting": setting,
            "narrative": narrative,
            "generator": source,
            "voice_cast": voice_cast,
            "voice_cast_source": voice_cast_source,
            "hospital_example": "江苏省人民医院",
            "smart_consultation_channel": "省人医微信公众号",
            "insurance_resources": [
                {"title": "2024级新生大学生医保通知", "url": "/static/insurance/njmu-2024-new-student-insurance-notice.pdf"},
                {"title": "学生医保政策解答手册", "url": "/static/insurance/njmu-student-insurance-faq-2023.docx"},
                {"title": "南京医科大学大学生医保简介", "url": "/static/insurance/njmu-student-insurance-introduction.docx"},
            ],
            "initial_visit_check_in_flow": ["自助机打印报到单", "诊间报到机扫码", "排队候诊"],
            "follow_up_check_in_flow": ["使用初诊报到单", "诊间报到机扫码", "排队候诊"],
            "ordinary_order_execution_flow": ["医生开具医嘱", "人工收费窗口缴费", "取药或检查治疗"],
            "emergency_order_execution_flow": ["急诊绿色通道", "紧急检查、抢救或治疗", "病情稳定后补办缴费结算"],
            "pacing": {
                "mode": "accelerated",
                "required_user_checkpoints": (
                    ["急诊分诊与关键症状表达", "紧急检查或治疗配合", "病情稳定后的后续安排"]
                    if case.get("urgent")
                    else [
                        "挂号选科",
                        "自助机打印报到单与诊间报到机扫码",
                        "核心症状表达",
                        "用药安全确认",
                        "人工收费窗口缴费与医保决策",
                    ]
                ),
                "auto_advance_steps": (
                    ["急危重症的紧急检查、抢救或治疗过场", "病情稳定后的补缴费与结算"]
                    if case.get("urgent")
                    else [
                        "建档核验",
                        "扫码报到后的候诊叫号",
                        "人工缴费后的检查与等待",
                        "人工缴费后的取药、治疗或手术等体验性过程",
                    ]
                ),
                "target_user_turns": "6-8",
            },
        },
    }


def _choking_context(previous_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    recent_signatures = {item.get("signature") for item in previous_contexts[-3:]}
    combinations = [
        (character, location, foreign_object)
        for character in CHOKING_CHARACTERS
        for location in CHOKING_LOCATIONS
        for foreign_object in CHOKING_OBJECTS
        if f"{character}|{location}" not in recent_signatures
    ]
    character, location, foreign_object = _random.choice(combinations or [
        (_random.choice(CHOKING_CHARACTERS), _random.choice(CHOKING_LOCATIONS), _random.choice(CHOKING_OBJECTS))
    ])
    # 第3次及以后的训练，有概率遇到特殊患者（孕妇/肥胖），考察胸部冲击
    special_case = None
    if len(previous_contexts) >= 2 and _random.random() < 0.5:
        special_case = _random.choice(CHOKING_SPECIAL_CASES)
        character = special_case["character"]
    immutable_fact = "无法发出声音，双手紧紧掐住脖子，脸色迅速变得青紫"
    # 只描述可观察到的体征，不直接说患者被什么噎住（用户在现场无从得知），
    # 异物以"桌上没吃完的食物"这一环境线索出现
    base_description = (
        f"你正在{location}，旁边一位{character}突然猛地捂住喉咙：对方{immutable_fact}，"
        f"神情极度惊恐，双手在空中慌乱抓挠。他身旁的桌上还放着一包没吃完的{foreign_object}。"
    )
    narrative, source = _refine_narrative(base_description, immutable_fact, "异物梗阻急救")
    context = {
        "scene_type": "choking",
        "character": character,
        "location": location,
        "foreign_object": foreign_object,
        "signature": f"{character}|{location}",
        "narrative": narrative,
        "generator": source,
        "deterioration_after": _random.randint(60, 90),
        # 即使已开始施救也持续计时，直到患者明确咳出异物；在原阈值上延长 30 秒。
        "collapse_after": _random.randint(150, 180),
    }
    if special_case:
        # 仅供各智能体内部使用的特殊情境说明，不出现在开场白里
        context["special_note"] = special_case["note"]
    return {
        "opening_message": f"{narrative}\n\n你现在就在现场。请观察并说出你的第一步行动。",
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "quick_actions": [],
            "character": character,
            "location": location,
            "foreign_object": foreign_object,
            "is_special": bool(special_case),
            "special_note": special_case["note"] if special_case else None,
        },
        "context": context,
    }


OSCE_FIXED_OPENING_VARIANTS = (
    "上午的内科 OSCE 模拟考站已经开始，一位因反复不适前来就诊的年轻女性正在等候。",
    "你进入内科 OSCE 模拟考站，面前坐着一位因不适前来就诊的年轻女性。",
    "本轮内科 OSCE 模拟已开场，诊室内一位年轻女性正等待你完成接诊。",
)

OSCE_FALLBACK_CASES = (
    {
        "scenario_id": "OSCE-AUTO-F01",
        "patient": "24岁女性，公司职员",
        "chief_problem": "心悸、怕热、多汗伴体重下降2个月",
        "history_clues": ["食欲增加", "易焦虑和失眠", "月经量减少"],
        "key_findings": ["静息心率112次/分", "手指细颤", "甲状腺弥漫性肿大", "TSH降低、FT4升高"],
        "reference_diagnosis": ["甲状腺功能亢进症", "Graves病"],
    },
    {
        "scenario_id": "OSCE-AUTO-F02",
        "patient": "20岁女性，大学生",
        "chief_problem": "乏力、头晕伴活动后心悸3个月",
        "history_clues": ["月经量较多", "食欲下降", "无黑便或呕血"],
        "key_findings": ["面色和结膜苍白", "心率98次/分", "血红蛋白82g/L", "MCV降低、血清铁蛋白降低"],
        "reference_diagnosis": ["缺铁性贫血"],
    },
    {
        "scenario_id": "OSCE-AUTO-F03",
        "patient": "27岁男性，研究生",
        "chief_problem": "反复上腹痛3个月，近1周加重",
        "history_clues": ["空腹时明显", "进食后可缓解", "无呕血或黑便"],
        "key_findings": ["上腹轻压痛", "无反跳痛", "血常规无明显异常", "尿素呼气试验阳性"],
        "reference_diagnosis": ["十二指肠溃疡", "幽门螺杆菌感染"],
    },
)


def _clean_osce_case(payload: Any) -> dict[str, Any] | None:
    """仅接受完整、短小的结构化病例。"""
    if not isinstance(payload, dict):
        return None
    cleaned: dict[str, Any] = {}
    for key in ("scenario_id", "patient", "chief_problem"):
        value = str(payload.get(key) or "").strip()
        if not value or len(value) > 180:
            return None
        cleaned[key] = value
    for key in ("history_clues", "key_findings", "reference_diagnosis"):
        values = payload.get(key)
        if not isinstance(values, list):
            return None
        items = [str(item).strip() for item in values if str(item).strip()]
        if not items or len(items) > 8 or any(len(item) > 100 for item in items):
            return None
        cleaned[key] = items
    return cleaned


def _case_repeats_history(case: dict[str, Any], previous_contexts: list[dict[str, Any]]) -> bool:
    """在本地对比重复度，不向模型发送任何历史病例内容。"""
    case_id = case.get("scenario_id")
    diagnoses = {str(item).strip().lower() for item in case.get("reference_diagnosis", [])}
    for previous in previous_contexts:
        old_case = previous.get("hidden_case") or {}
        old_diagnoses = {str(item).strip().lower() for item in old_case.get("reference_diagnosis", [])}
        if case_id and case_id == previous.get("scenario_id"):
            return True
        if diagnoses & old_diagnoses:
            return True
    return False


def _generate_osce_case(previous_contexts: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    prompt = """你是高校医学生 OSCE 问诊训练的场景生成智能体。
请自主生成一个新的内科标准化病人病例。

生成原则：
1. 选择18岁以上常见内科疾病，难度为高校 OSCE 综合站5星；
2. 问诊是训练重点，必须有可通过追问获得的有区分度线索；
3. 主诉、病史、体征、检查与诊断必须互相一致，不设计需要立即抢救的危重症；
4. 不要夹带教学解释、Markdown 或标准答案提示。

仅返回合法 JSON：
{
  "scenario_id": "OSCE-AUTO-唯一英数编号",
  "patient": "年龄、性别和身份",
  "chief_problem": "规范主诉",
  "history_clues": ["2至5条需追问线索"],
  "key_findings": ["3至6条快速给出的关键查体或辅助检查"],
  "reference_diagnosis": ["1至3项初步诊断"]
}
"""
    try:
        cleaned = _clean_osce_case(llm.call_llm_json([], prompt, llm.CHAT_REASONING_EFFORT))
        if cleaned and not _case_repeats_history(cleaned, previous_contexts):
            return cleaned, "agent_generated"
    except Exception as exc:
        logger.info("OSCE 场景生成智能体不可用，使用备用病例：%s", exc)

    recent_ids = {item.get("scenario_id") for item in previous_contexts[-3:]}
    fallback = _choose_without_recent(list(OSCE_FALLBACK_CASES), recent_ids, key=lambda item: item["scenario_id"])
    return json.loads(json.dumps(fallback, ensure_ascii=False)), "validated_fallback"


def _osce_context(previous_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    """首训用固定病例小幅变化开场；第二次起生成新病例。"""
    training_round = len(previous_contexts) + 1
    if not previous_contexts:
        hidden_case = {
            "patient": "21岁女性，农民，江苏句容人",
            "chief_problem": "反复心慌、气喘、下肢浮肿3年，加重1周",
            "history_clues": ["反复咽痛", "关节痛"],
            "key_findings": [
                "端坐呼吸", "颈静脉怒张", "双肺底湿啰音", "心律绝对不齐",
                "心尖部收缩期及舒张期杂音", "腹水", "下肢凹陷性水肿",
            ],
            "reference_diagnosis": [
                "风湿性心脏病：二尖瓣狭窄并关闭不全",
                "心房颤动", "心功能不全", "慢性扁桃体炎", "肠蛔虫感染",
            ],
        }
        scenario_id = "OSCE-IM-01"
        generator = "fixed_case_variant"
        variant_index = _random.randrange(len(OSCE_FIXED_OPENING_VARIANTS))
        opening_lead = OSCE_FIXED_OPENING_VARIANTS[variant_index]
    else:
        hidden_case, generator = _generate_osce_case(previous_contexts)
        scenario_id = hidden_case.pop("scenario_id")
        variant_index = None
        opening_lead = "你进入一个新的内科 OSCE 模拟考站，一位因不适前来就诊的成年患者正在等候。"

    opening = (
        f"{opening_lead}"
        "本考站以问诊为重点；问诊结束后，体格检查与辅助检查会由考官快速给出关键结果。\n\n"
        "请以接诊医生身份开始问诊，并在右侧病历区同步整理问诊信息。"
    )
    return {
        "opening_message": opening,
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "scenario_id": scenario_id,
            "first_step": "规范问候并核对患者身份",
            "quick_actions": [],
        },
        "context": {
            "scene_type": "osce",
            "scenario_id": scenario_id,
            "training_round": training_round,
            "generator": generator,
            "fixed_variant": variant_index,
            "station": "内科问诊与病历书写",
            "focus": "问诊",
            "exam_mode": "用户提出一项合理查体或辅助检查后，考官一次性简要给出关键结果并快速进入病历书写",
            "hidden_case": hidden_case,
            "interview_framework": [
                "接诊准备与一般资料", "主诉", "现病史", "既往史和过敏史",
                "系统回顾", "个人婚育月经史", "家族史",
            ],
            "record_requirements": [
                "基本信息", "主诉", "现病史", "其他病史", "体格检查", "辅助检查",
                "病历摘要", "初步诊断与鉴别诊断",
            ],
            "target_user_turns": "8-12",
        },
    }


def generate_scene_context(
    scene: Any,
    scene_type: str,
    gender: str = "unspecified",
    previous_contexts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成可展示的开场消息和供后续智能体使用的内部场景上下文。"""
    previous_contexts = previous_contexts or []
    if scene_type == "first_visit":
        return _first_visit_context(gender, previous_contexts)
    if scene_type == "choking":
        return _choking_context(previous_contexts)
    if scene_type == "osce":
        return _osce_context(previous_contexts)

    opening = getattr(scene, "opening_message", None) or getattr(scene, "background", None) or "训练开始。"
    return {
        "opening_message": opening,
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "first_step": "观察场景并开始沟通",
            "quick_actions": [],
        },
        "context": {
            "scene_type": scene_type,
            "narrative": opening,
            "generator": "template",
            "scene_config": json.loads(json.dumps(getattr(scene, "config", None) or {}, ensure_ascii=False)),
        },
    }
