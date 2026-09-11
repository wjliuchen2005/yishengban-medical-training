import asyncio
import base64
import io
import json
import wave
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import ChatMessage, ChatSession, Scene, User, DailyUsage
from app.routers import voice
from app.routers.chat import _history_for_llm, _coach_history_for_llm
from app.routers.result import _build_transcript
from app.routers.psych import PsychMessage, PsychSaveRequest, save_psych_session, get_psych_session
from app.voice import VoiceAssessment, sign_assessment, verify_assessments, with_voice


def wav(seconds=2, rate=16000):
    out = io.BytesIO()
    with wave.open(out, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes(b'\0\0' * int(seconds * rate))
    return base64.b64encode(out.getvalue()).decode()


@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add_all([User(id=1, username='student', password_hash='test'), Scene(id=1, title='OSCE模拟问诊', role='标准化患者'), ChatSession(id=1, user_id=1, scene_id=1)])
        session.commit()
        yield session
    engine.dispose()


@pytest.mark.parametrize('data', ['not base64!', wav(.05), wav(91), wav(2, 48000)])
def test_wav_rejects_invalid_or_unbounded(data):
    with pytest.raises(HTTPException): voice.decode_wav(data)


def test_wav_accepts_bounded_pcm():
    assert voice.decode_wav(wav())[1] == 2


def test_signature_and_account_scope():
    data = {'id': 'clip', 'status': 'limited', 'impression': '片段太短'}
    receipt = sign_assessment(1, 'chat:1', data)
    assert verify_assessments([receipt, receipt], 1, 'chat:1') == [data]
    for user, scope, token in [(2, 'chat:1', receipt), (1, 'chat:2', receipt), (1, 'chat:1', receipt + 'x')]:
        with pytest.raises(HTTPException): verify_assessments([token], user, scope)
    with pytest.raises(HTTPException): verify_assessments([{}], 1, 'chat:1')


def test_limited_feedback_cannot_score():
    result = VoiceAssessment(status='limited', score=82, dimensions={'warmth': 90}, impression='评价意义不大')
    assert result.score is None and result.dimensions == {}
    with pytest.raises(ValueError): VoiceAssessment(status='assessed', impression='x', dimensions={'gender': 70})


def test_context_ownership_and_full_history(db):
    db.add_all([ChatMessage(session_id=1, role='user', content='第'+str(i)+'条') for i in range(45)])
    db.commit()
    user = db.get(User, 1)
    req = voice.AudioRequest(audio=wav(), session_id=1)
    scope, context = voice.voice_context(req, db, user)
    assert scope == 'chat:1' and len(context['messages']) == 45
    assert context['user_role'] == '接诊医学生'
    with pytest.raises(HTTPException): voice.voice_context(req, db, SimpleNamespace(id=2))


def test_feedback_reaches_conversation_coach_and_scorer():
    m = SimpleNamespace(id=1, role='user', content='编辑后的内容', extra={'voice_assessments': [{'id':'first'}, {'id':'second'}]})
    for history in [_history_for_llm([m]), _coach_history_for_llm([m])]:
        assert '编辑后的内容' in history[0]['content'] and 'second' in history[0]['content']
    assert len(_build_transcript([m])[0]['voice_assessments']) == 2
    assert with_voice('仅文字', []) == '仅文字'


def test_psych_save_encrypts_feedback_and_restores_receipt(db):
    data = {'id':'one', 'status':'limited', 'impression':'测试声音反馈'}
    token = sign_assessment(1, 'psych', data)
    user = db.get(User, 1)
    req = PsychSaveRequest(messages=[PsychMessage(role='user', content='私密内容', voice_receipts=[token])])
    saved = asyncio.run(save_psych_session(req, db, user))
    restored = asyncio.run(get_psych_session(saved['id'], db, user))
    assert restored['messages'][0]['voice_assessments'] == [data]
    assert restored['messages'][0]['voice_receipts'] == [token]


def test_psych_save_updates_loaded_session_in_place(db):
    user = db.get(User, 1)
    first = asyncio.run(save_psych_session(PsychSaveRequest(messages=[PsychMessage(role='user', content='第一段')]), db, user))
    updated = asyncio.run(save_psych_session(PsychSaveRequest(session_id=first['id'], messages=[PsychMessage(role='user', content='第一段'), PsychMessage(role='assistant', content='我在听'), PsychMessage(role='user', content='第二段')]), db, user))
    restored = asyncio.run(get_psych_session(first['id'], db, user))
    assert updated['id'] == first['id'] and updated['updated'] is True
    assert [message['content'] for message in restored['messages']] == ['第一段', '我在听', '第二段']


@pytest.mark.parametrize('finished', [True, False])
def test_asr_stream_failure_is_explicit_and_text_survives(db, finished):
    real_client = httpx.AsyncClient
    events = 'data: '+json.dumps({'choices':[{'delta':{'content':'您好，我想咨询一下。'}}]})+'\n\n'
    if finished: events += 'data: [DONE]\n\n'
    def handler(request):
        payload = json.loads(request.content)
        assert payload['model'] == 'mimo-v2.5-asr' and payload['stream'] is True
        return httpx.Response(200, text=events)
    async def run():
        with patch.object(voice.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)), patch.dict('os.environ', {'MIMO_API_KEY':'fake'}):
            response = await voice.transcribe(voice.AudioRequest(audio=wav(), session_id=1), db.get(User, 1), db)
            return ''.join([part async for part in response.body_iterator])
    output = asyncio.run(run())
    assert '您好' in output
    assert ('"type": "done"' in output) == finished
    assert ('"type": "error"' in output) != finished
    assert db.query(DailyUsage).first().cost_micrormb > 0


@pytest.mark.parametrize('valid', [True, False])
def test_assessment_json_validation_and_safe_unavailable(db, valid):
    real_client = httpx.AsyncClient
    def handler(request):
        payload = json.loads(request.content)
        assert payload['model'] == 'mimo-v2.5'
        assert 'input_audio' in str(payload['messages'])
        content = json.dumps({'status':'assessed', 'score':80, 'confidence':.8, 'emotion':'平稳', 'impression':'语速平稳', 'evidence':['停顿自然']}) if valid else 'not json'
        return httpx.Response(200, json={'choices':[{'message':{'content':content}}]})
    async def run():
        with patch.object(voice.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)), patch.dict('os.environ', {'MIMO_API_KEY':'fake'}):
            return await voice.assess(voice.AudioRequest(audio=wav(), session_id=1), db.get(User, 1), db)
    result = asyncio.run(run())
    assert result['assessment']['status'] == ('assessed' if valid else 'unavailable')
    assert verify_assessments([result['receipt']], 1, 'chat:1')[0] == result['assessment']
