"""动态训练情景生成。

核心病例和急救体征来自功能说明中的审核池；大模型只负责润色生活化细节，
不能改变核心症状、训练目标或正确处置。大模型不可用时使用本地模板，保证开场可用。
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

    base_description = (
        f"{setting}，你发现自己{case['symptoms']}。你第一次需要独自处理就医流程，"
        "身边暂时没有家人或同学陪同。"
    )
    narrative, source = _refine_narrative(
        base_description,
        case["symptoms"],
        "第一次独立看病",
    )

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
                "label": "省人医微信公众号智能问诊",
                "value": "我不确定该挂哪个科，先打开省人医微信公众号使用智能问诊。",
            },
        ]
        guidance = (
            "你的第一步是选择挂号方式和科室：可以线上预约或线下挂号；"
            "如果不确定科室，可以在【省人医微信公众号】先使用智能问诊。"
        )

    return {
        "opening_message": f"{narrative}\n\n{guidance}请告诉我你准备怎么做。",
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "scenario_id": case["scenario_id"],
            "first_step": first_step,
            "quick_actions": actions,
        },
        "context": {
            "scene_type": "first_visit",
            "scenario_id": case["scenario_id"],
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
            "hospital_example": "江苏省人民医院",
            "smart_consultation_channel": "省人医微信公众号",
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
        "collapse_after": _random.randint(120, 150),
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


def _osce_context() -> dict[str, Any]:
    """固定 OSCE 考站。病例细节只放在内部上下文，按学生问到的内容逐步释放。"""
    opening = (
        "你进入内科 OSCE 模拟考站，面前坐着一位因不适前来就诊的年轻女性。"
        "本考站以问诊为重点；问诊结束后，体格检查与辅助检查会由考官快速给出关键结果。\n\n"
        "请以接诊医生身份开始问诊，并在结束前打开“病历记录”完成书写。"
    )
    return {
        "opening_message": opening,
        "opening_meta": {
            "kind": "scene_intro",
            "agent_name": "情景生成智能体",
            "scenario_id": "OSCE-IM-01",
            "first_step": "规范问候并核对患者身份",
            "quick_actions": [],
        },
        "context": {
            "scene_type": "osce",
            "station": "内科问诊与病历书写",
            "focus": "问诊",
            "exam_mode": "用户提出一项合理查体或辅助检查后，考官一次性简要给出关键结果并快速进入病历书写",
            "hidden_case": {
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
            },
            "interview_framework": [
                "接诊准备与一般资料", "主诉", "现病史", "既往史和过敏史",
                "系统回顾", "个人婚育月经史", "家族史",
            ],
            "record_requirements": [
                "主诉", "现病史", "其他病史", "体格检查", "辅助检查",
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
        return _osce_context()

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
