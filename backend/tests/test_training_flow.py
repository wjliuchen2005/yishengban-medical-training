import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.prompts import STAGE_CATALOG, build_patient_system_prompt, get_initial_stage, get_scene_type
from app.ai.scenario_generator import generate_scene_context
from app.database import Base
from app.models import ChatMessage, ChatSession, Result, Scene, User
from app.routers.chat import (
    _build_ui_action,
    _delete_session_records,
    _fallback_stage_info,
    _history_for_llm,
    _normalize_stage_info,
    _time_pressure_status,
)
from app.routers import result as result_router
from app.routers.result import _fallback_rating


def make_scene(title: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        title=title,
        description="训练场景",
        role="旧角色",
        background="旧数据库背景",
        opening_message="旧患者开场白",
        config=None,
    )


class ScenarioGeneratorTests(unittest.TestCase):
    @patch("app.ai.scenario_generator.llm.call_llm_json", side_effect=RuntimeError("offline"))
    def test_first_visit_opens_with_scene_not_patient_dialogue(self, _mock_llm):
        generated = generate_scene_context(make_scene("第一次独立看病"), "first_visit", "male", [])

        self.assertIn("你的第一步", generated["opening_message"])
        self.assertIn(generated["context"]["symptoms"], generated["opening_message"])
        self.assertEqual(generated["context"]["scenario_id"], "S00")
        self.assertEqual(generated["context"]["case_group"], "intro")
        self.assertNotIn("头痛", generated["context"]["symptoms"])
        self.assertNotIn(generated["context"]["scenario_id"], {"S05", "S09"})
        self.assertEqual(generated["opening_meta"]["kind"], "scene_intro")
        self.assertGreaterEqual(len(generated["opening_meta"]["quick_actions"]), 2)
        self.assertNotIn("【流程说明】", generated["opening_message"])
        self.assertNotIn("报到单", generated["opening_message"])
        self.assertNotIn("人工收费窗口", generated["opening_message"])
        self.assertEqual(generated["context"]["hospital_example"], "江苏省人民医院")
        self.assertEqual(generated["context"]["smart_consultation_channel"], "省人医微信公众号")
        self.assertIn("自助机打印报到单", generated["context"]["initial_visit_check_in_flow"])
        self.assertIn("人工收费窗口缴费", generated["context"]["ordinary_order_execution_flow"])
        self.assertTrue(any("省人医微信公众号" in action["label"] for action in generated["opening_meta"]["quick_actions"]))
        self.assertFalse(any("智能问诊" in item for item in generated["context"]["pacing"]["required_user_checkpoints"]))

    @patch("app.ai.scenario_generator.llm.call_llm_json", side_effect=RuntimeError("offline"))
    def test_first_visit_curriculum_delays_special_cases(self, _mock_llm):
        scene = make_scene("第一次独立看病")
        second = generate_scene_context(
            scene,
            "first_visit",
            "male",
            [{"scenario_id": "S00", "case_group": "intro", "setting": "场景A"}],
        )
        fourth = generate_scene_context(
            scene,
            "first_visit",
            "male",
            [
                {"scenario_id": "S00", "case_group": "intro", "setting": "场景A"},
                {"scenario_id": "S02", "case_group": "common", "setting": "场景B"},
                {"scenario_id": "S04", "case_group": "common", "setting": "场景C"},
            ],
        )

        self.assertEqual(second["context"]["case_group"], "common")
        self.assertEqual(second["context"]["training_round"], 2)
        self.assertEqual(fourth["context"]["case_group"], "special")
        self.assertEqual(fourth["context"]["training_round"], 4)

    @patch("app.ai.scenario_generator.llm.call_llm_json", side_effect=RuntimeError("offline"))
    def test_choking_scene_has_medical_signs_and_time_pressure(self, _mock_llm):
        generated = generate_scene_context(make_scene("异物梗阻急救"), "choking", "unspecified", [])

        self.assertIn("无法发出声音", generated["opening_message"])
        self.assertIn("脸色迅速变得青紫", generated["opening_message"])
        self.assertGreaterEqual(generated["context"]["deterioration_after"], 60)
        self.assertLessEqual(generated["context"]["collapse_after"], 150)

    def test_osce_scene_prioritizes_interview_and_hides_case_answer(self):
        scene = make_scene("OSCE模拟问诊与病历书写")
        generated = generate_scene_context(scene, get_scene_type(scene), "unspecified", [])

        self.assertEqual(generated["context"]["focus"], "问诊")
        self.assertIn("快速", generated["context"]["exam_mode"])
        self.assertIn("规范问候", generated["opening_meta"]["first_step"])
        self.assertNotIn("风湿性心脏病", generated["opening_message"])


class PromptAndStageTests(unittest.TestCase):
    def test_first_visit_prompt_keeps_user_as_patient(self):
        prompt = build_patient_system_prompt(
            make_scene("第一次独立看病"),
            "first_visit",
            {"symptoms": "发热2天", "correct_departments": ["内科"]},
            get_initial_stage("first_visit"),
        )

        self.assertIn("医院流程角色", prompt)
        self.assertIn("绝不能把用户当成医生", prompt)
        self.assertIn("发热2天", prompt)
        self.assertIn("采用加速训练", prompt)
        self.assertIn("不得问“准备好了吗”", prompt)
        self.assertIn("江苏省人民医院", prompt)
        self.assertIn("省人医微信公众号", prompt)
        self.assertIn("智能问诊是可选", prompt)
        self.assertIn("复诊时可使用初诊报到单", prompt)
        self.assertIn("人工收费窗口", prompt)
        self.assertIn("不得输出“【流程说明】”", prompt)
        self.assertIn("疑似脑出血", prompt)
        self.assertIn("先救治，后结算", prompt)

    def test_osce_prompt_makes_exam_a_fast_transition(self):
        prompt = build_patient_system_prompt(
            make_scene("OSCE模拟问诊与病历书写"),
            "osce",
            {"focus": "问诊"},
            get_initial_stage("osce"),
        )
        self.assertIn("本训练重心是问诊", prompt)
        self.assertIn("不得要求学生逐项操作", prompt)
        self.assertIn("不得一次性泄露隐藏病例", prompt)

    def test_stage_payload_is_clamped_and_named_from_catalog(self):
        current = get_initial_stage("first_visit")
        normalized = _normalize_stage_info(
            {"stage": 2, "name": "错误名称", "progress": 130},
            "first_visit",
            current,
        )

        self.assertEqual(normalized["id"], 2)
        self.assertEqual(normalized["name"], "症状问诊")
        self.assertEqual(normalized["progress"], 100)
        self.assertTrue(normalized["transitioned"])

    def test_first_visit_stage_catalog_uses_required_hospital_order(self):
        self.assertEqual(
            [stage["name"] for stage in STAGE_CATALOG["first_visit"]],
            ["挂号报到", "症状问诊", "诊断医嘱", "人工缴费", "取药执行"],
        )

    def test_first_visit_fallback_does_not_skip_check_in_or_manual_window(self):
        initial = get_initial_stage("first_visit")
        registration_only = [SimpleNamespace(role="user", content="我已经线上预约挂号内科。")]
        still_checking_in = _fallback_stage_info(registration_only, "first_visit", initial)
        self.assertEqual(still_checking_in["id"], 1)

        completed_check_in = [
            SimpleNamespace(
                role="user",
                content="我预约挂号内科，到自助机打印报到单，再到诊间报到机扫码报到。",
            )
        ]
        entered_consultation = _fallback_stage_info(completed_check_in, "first_visit", initial)
        self.assertEqual(entered_consultation["id"], 2)

        diagnosis_stage = {**STAGE_CATALOG["first_visit"][2], "progress": 20}
        payment_without_window = [SimpleNamespace(role="user", content="我想用医保支付。")]
        still_needs_window = _fallback_stage_info(payment_without_window, "first_visit", diagnosis_stage)
        self.assertEqual(still_needs_window["id"], 3)

        manual_payment = [SimpleNamespace(role="user", content="我到人工收费窗口用医保完成缴费。")]
        paid = _fallback_stage_info(manual_payment, "first_visit", diagnosis_stage)
        self.assertEqual(paid["id"], 4)

    def test_first_visit_emergency_fallback_allows_care_before_payment(self):
        diagnosis_stage = {**STAGE_CATALOG["first_visit"][2], "progress": 20}
        urgent_care = [
            SimpleNamespace(role="system", content="突发从未有过的剧烈头痛并呕吐。"),
            SimpleNamespace(role="user", content="我立即去急诊分诊。"),
            SimpleNamespace(role="ai", content="疑似脑出血，立即进入绿色通道做头颅CT并抢救。"),
        ]
        care_started = _fallback_stage_info(urgent_care, "first_visit", diagnosis_stage)
        self.assertEqual(care_started["id"], 4)

        treatment_stage = {**STAGE_CATALOG["first_visit"][3], "progress": 20}
        stabilized = urgent_care + [SimpleNamespace(role="ai", content="紧急手术完成，术后病情稳定，后续再补办结算。")]
        care_completed = _fallback_stage_info(stabilized, "first_visit", treatment_stage)
        self.assertEqual(care_completed["id"], 5)

    def test_heimlich_name_only_opens_action_form(self):
        action = _build_ui_action("choking", "我给他做海姆立克", None)
        self.assertEqual(action["type"], "describe_action")
        self.assertEqual(len(action["fields"]), 3)

    def test_stage_restart_discards_old_roleplay_context(self):
        messages = [
            SimpleNamespace(role="user", content="旧回答", extra=None),
            SimpleNamespace(role="ai", content="旧回复", extra=None),
            SimpleNamespace(role="system", content="重置", extra={"kind": "stage_restart"}),
            SimpleNamespace(role="user", content="新回答", extra=None),
        ]
        self.assertEqual(_history_for_llm(messages), [{"role": "user", "content": "新回答"}])

    def test_medical_record_is_not_sent_back_to_patient_agent(self):
        messages = [
            SimpleNamespace(role="user", content="您哪里不舒服？", extra=None),
            SimpleNamespace(role="user", content="【病历记录】\n主诉：心慌3年", extra={"kind": "medical_record"}),
        ]
        self.assertEqual(_history_for_llm(messages), [{"role": "user", "content": "您哪里不舒服？"}])

    def test_time_pressure_stops_after_patient_coughs_out_foreign_body(self):
        session = SimpleNamespace(started_at=datetime.utcnow() - timedelta(seconds=300))
        messages = [
            SimpleNamespace(role="user", content="我继续按刚才的方法施救", extra=None),
            SimpleNamespace(
                role="ai",
                content="患者突然咳出异物，正弯腰大口喘气，脸色逐渐恢复。",
                extra={"stage_info": {"id": 2}},
            ),
        ]

        pressure = _time_pressure_status(
            session,
            "choking",
            {"deterioration_after": 60, "collapse_after": 120},
            messages,
        )

        self.assertIsNone(pressure)

    def test_time_pressure_does_not_treat_negated_recovery_as_resolved(self):
        session = SimpleNamespace(started_at=datetime.utcnow() - timedelta(seconds=300))
        messages = [
            SimpleNamespace(role="user", content="我先观察情况", extra=None),
            SimpleNamespace(
                role="ai",
                content="患者仍未咳出异物，继续窒息，脸色更加青紫。",
                extra={"stage_info": {"id": 2}},
            ),
        ]

        pressure = _time_pressure_status(
            session,
            "choking",
            {"deterioration_after": 60, "collapse_after": 120},
            messages,
        )

        self.assertIn("失去意识", pressure)


class DeleteTrainingRecordTests(unittest.TestCase):
    def test_delete_session_removes_messages_and_result_only_for_target(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            user = User(username="delete_test", password_hash="hash")
            scene = Scene(title="异物梗阻急救")
            db.add_all([user, scene])
            db.commit()
            target = ChatSession(user_id=user.id, scene_id=scene.id)
            retained = ChatSession(user_id=user.id, scene_id=scene.id)
            db.add_all([target, retained])
            db.commit()
            db.add_all([
                ChatMessage(session_id=target.id, role="user", content="目标消息"),
                ChatMessage(session_id=retained.id, role="user", content="保留消息"),
                Result(session_id=target.id, user_id=user.id, total_score=80),
                Result(session_id=retained.id, user_id=user.id, total_score=90),
            ])
            db.commit()

            deleted = _delete_session_records(db, target)
            db.commit()

            self.assertEqual(deleted, {"messages": 1, "results": 1})
            self.assertIsNone(db.get(ChatSession, target.id))
            self.assertEqual(db.query(ChatMessage).filter_by(session_id=target.id).count(), 0)
            self.assertEqual(db.query(Result).filter_by(session_id=target.id).count(), 0)
            self.assertIsNotNone(db.get(ChatSession, retained.id))
            self.assertEqual(db.query(ChatMessage).filter_by(session_id=retained.id).count(), 1)
            self.assertEqual(db.query(Result).filter_by(session_id=retained.id).count(), 1)
        finally:
            db.close()
            engine.dispose()


class RatingRecoveryTests(unittest.TestCase):
    def setUp(self):
        with result_router._rating_lock:
            result_router._rating_tasks.clear()

    def tearDown(self):
        with result_router._rating_lock:
            result_router._rating_tasks.clear()

    @patch.object(result_router, "RATING_TASK_STALE_SECONDS", 90.0)
    def test_stale_rating_task_can_be_reclaimed_without_old_task_releasing_new_one(self):
        first_claim = result_router._claim_rating_task(7, now=100.0)
        self.assertEqual(first_claim, (100.0, False))
        self.assertIsNone(result_router._claim_rating_task(7, now=150.0))

        recovered_claim = result_router._claim_rating_task(7, now=191.0)
        self.assertEqual(recovered_claim, (191.0, True))

        result_router._release_rating_task(7, 100.0)
        self.assertEqual(result_router._rating_tasks[7], 191.0)
        result_router._release_rating_task(7, 191.0)
        self.assertNotIn(7, result_router._rating_tasks)

    @patch("app.routers.result.llm.call_llm_json", side_effect=TimeoutError("network interrupted"))
    def test_rating_timeout_is_bounded_and_fallback_is_persisted(self, mock_llm):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            user = User(username="rating_recovery", password_hash="hash")
            scene = Scene(title="第一次独立看病")
            db.add_all([user, scene])
            db.commit()
            session = ChatSession(user_id=user.id, scene_id=scene.id, ended_at=datetime.utcnow())
            db.add(session)
            db.commit()
            db.add(ChatMessage(session_id=session.id, role="user", content="我先线上挂号内科。"))
            db.commit()
            messages = db.query(ChatMessage).filter_by(session_id=session.id).all()

            rating = result_router._generate_rating(db, session, scene, messages)

            self.assertEqual(rating["rating_source"], "rules")
            self.assertEqual(db.query(Result).filter_by(session_id=session.id).count(), 1)
            self.assertEqual(session.is_rated, 1)
            self.assertEqual(mock_llm.call_args.kwargs["timeout_seconds"], result_router.RATING_REQUEST_TIMEOUT_SECONDS)
            self.assertEqual(mock_llm.call_args.kwargs["max_retries"], 0)
        finally:
            db.close()
            engine.dispose()


class RatingFallbackTests(unittest.TestCase):
    def test_first_visit_fallback_returns_explainable_scores(self):
        messages = [
            SimpleNamespace(role="system", content="场景开始"),
            SimpleNamespace(role="user", content="您好，我想线上预约内科。我发热2天，最高38.5度，还伴有头痛。"),
            SimpleNamespace(role="ai", content="请问有没有药物过敏？"),
            SimpleNamespace(role="user", content="没有药物过敏。请问药怎么吃，有什么副作用？可以用医保吗？"),
        ]

        rating = _fallback_rating("first_visit", messages)

        self.assertEqual(rating["rating_source"], "rules")
        self.assertGreater(rating["dimensions"]["accuracy"], 0)
        self.assertGreater(rating["sample_completeness"]["symptoms"], 0)
        self.assertTrue(rating["decision_tree"]["optimal_path"])

    def test_emergency_rating_does_not_require_payment_before_care(self):
        messages = [
            SimpleNamespace(role="system", content="突发从未有过的剧烈头痛、呕吐和视物模糊。"),
            SimpleNamespace(role="user", content="我立即去急诊分诊，说明症状是刚才突然开始并配合紧急检查。"),
            SimpleNamespace(role="ai", content="疑似脑出血，立即进入绿色通道做头颅CT并抢救。"),
            SimpleNamespace(role="user", content="请先救治，我听从安排并配合治疗。"),
        ]

        rating = _fallback_rating("first_visit", messages)

        self.assertEqual(rating["decision_tree"]["optimal_path"][0], "急诊分诊")
        self.assertFalse(any("人工收费窗口" in mistake for mistake in rating["key_mistakes"]))
        self.assertTrue(any("优先急诊检查和救治" in item for item in rating["highlights"]))

    def test_osce_fallback_scores_interview_and_independent_record(self):
        messages = [
            SimpleNamespace(role="system", content="OSCE考站", extra=None),
            SimpleNamespace(role="user", content="您好，我是接诊医生。请问姓名？哪里不舒服，多久了？什么时候开始，有什么诱因、加重缓解和伴随症状？", extra=None),
            SimpleNamespace(role="ai", content="我心慌气喘3年，最近加重。", extra=None),
            SimpleNamespace(role="user", content="既往有什么病？有无过敏、手术、输血？月经婚育和家族史如何？我申请生命体征、心肺听诊和心电图。", extra=None),
            SimpleNamespace(
                role="user",
                content="【病历记录】\n主诉：心慌气喘3年，加重1周。\n现病史：反复心慌气喘，活动后加重。\n其他病史：有反复咽痛。\n体格检查：心律不齐。\n辅助检查：心电图提示房颤。\n病历摘要：青年女性慢性病程急性加重。\n初步诊断：风湿性心脏病，心房颤动。",
                extra={"kind": "medical_record"},
            ),
        ]

        rating = _fallback_rating("osce", messages)

        self.assertGreater(rating["dimensions"]["accuracy"], 20)
        self.assertGreater(rating["osce_checklist"]["medical_record"], 80)
        self.assertIn("病历", rating["medical_record_review"])


if __name__ == "__main__":
    unittest.main()
