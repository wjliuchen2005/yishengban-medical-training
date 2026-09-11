/**
 * =====================================================
 * 心理陪伴相关 API
 * 后端：Python FastAPI  /api/psych
 *
 * 已接入：心理陪伴对话（无状态，历史由前端传回）
 * =====================================================
 */

import request from './request'

/**
 * @api {POST} /api/psych/chat 心理陪伴对话
 * @apiName PsychChat
 * @apiGroup Psych
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiBody {Array} messages 完整对话历史（不含 system），[{role:'user'|'assistant', content}]
 * @apiBody {String} messages.content 单条消息，最长 1000 字
 *
 * @apiSuccess {String} reply 陪伴回复
 * @apiSuccess {Boolean} crisis 是否命中危机信号（true 时前端应展示心理援助热线提示）
 *
 * @apiExample 前端调用：
 * const { reply, crisis } = await sendPsychMessage([
 *   { role: 'user', content: '最近压力好大' },
 *   { role: 'assistant', content: '听起来这段时间你扛了不少，愿意多说一点吗？' }
 * ])
 */
export function sendPsychMessage(messages) {
  return request({
    url: '/psych/chat',
    method: 'POST',
    data: { messages }
  })
}

export function savePsychSession(messages, sessionId = null) {
  return request({ url: '/psych/sessions', method: 'POST', data: { messages, session_id: sessionId } })
}

export function getPsychSessions() {
  return request({ url: '/psych/sessions', method: 'GET' })
}

export function getPsychSession(id) {
  return request({ url: `/psych/sessions/${id}`, method: 'GET' })
}

export function updatePsychSession(id, data) {
  return request({ url: `/psych/sessions/${id}`, method: 'PATCH', data })
}

export function deletePsychSession(id) {
  return request({ url: `/psych/sessions/${id}`, method: 'DELETE' })
}
