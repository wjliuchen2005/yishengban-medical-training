/**
 * =====================================================
 * 对话相关 API
 * 后端需实现：Python FastAPI
 * 路径前缀：/api/chat
 *
 * 已接入：患者/医院角色、观察者教练和阶段判断多智能体
 * =====================================================
 */

import request from './request'

/**
 * @api {POST} /api/chat/start 开始一个新对话会话
 * @apiName StartChat
 * @apiGroup Chat
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} scene_id 场景 ID
 *
 * @apiSuccess {Number} session_id 会话 ID
 * @apiSuccess {String} opening_message 角色开场白
 * @apiSuccess {Object} scene_info 场景信息
 */
export function startChat(sceneId, options = {}) {
  return request({
    url: '/chat/start',
    method: 'POST',
    data: { scene_id: Number(sceneId), ...options }
  })
}

/**
 * @api {POST} /api/chat/message 发送用户消息并获取 AI 回复
 * @apiName SendMessage
 * @apiGroup Chat
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} session_id 会话 ID
 * @apiParam {String} message 用户消息内容
 *
 * @apiSuccess {Number} message_id 消息 ID
 * @apiSuccess {String} role 'ai' | 'user' | 'coach'
 * @apiSuccess {String} content 消息内容
 * @apiSuccess {Number} timestamp 时间戳
 * @apiSuccess {Object} [coach_tip] 教练实时提示（如有）
 *
 * @apiExample 前端调用：
 * const res = await sendMessage({ session_id: 1, message: '您好，请描述症状' })
 * // res = {
 * //   message_id: 123,
 * //   role: 'ai',
 * //   content: '我最近咳嗽得很厉害...',
 * //   timestamp: 1692840000000,
 * //   coach_tip: { type: 'info', text: '注意询问咳嗽持续时间' }
 * // }
 */
export function sendMessage(data, options = {}) {
  return request({
    url: '/chat/message',
    method: 'POST',
    data,
    signal: options.signal
  })
}

/** 保存 OSCE 学生独立书写的病历记录（重复保存会更新同一条记录）。 */
export function saveMedicalRecord(sessionId, content) {
  return request({
    url: '/chat/record',
    method: 'POST',
    data: { session_id: sessionId, content }
  })
}

/**
 * @api {GET} /api/chat/session/:sessionId 获取会话详情
 * @apiName GetSession
 * @apiGroup Chat
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} session_id 会话 ID
 *
 * @apiSuccess {Object} session 会话详情
 * @apiSuccess {Array} session.messages 所有消息列表
 */
export function getSession(sessionId) {
  return request({
    url: `/chat/session/${sessionId}`,
    method: 'GET'
  })
}

/** 重新开始当前训练阶段，历史记录仍保留用于复盘。 */
export function restartChatStage(sessionId) {
  return request({
    url: '/chat/restart-stage',
    method: 'POST',
    data: { session_id: sessionId }
  })
}

/** 向观察者教练提问（教练只引导，不直接给标准答案）。 */
export function askCoach(sessionId, message, voiceReceipts = []) {
  return request({
    url: '/chat/coach',
    method: 'POST',
    data: { session_id: sessionId, message, voice_receipts: voiceReceipts }
  })
}

/** 时间压力轮询（仅异物梗阻场景）：超时未施救时患者会恶化/昏倒。 */
export function getSessionPressure(sessionId) {
  return request({
    url: `/chat/session/${sessionId}/pressure`,
    method: 'GET'
  })
}

/** 训练历史：历次会话与评分摘要。 */
export function getChatHistory() {
  return request({
    url: '/chat/history',
    method: 'GET'
  })
}

export function updateChatSessionFlags(sessionId, data) {
  return request({ url: `/chat/session/${sessionId}/flags`, method: 'PATCH', data })
}

export function getTrainingSummary() {
  return request({ url: '/chat/history/summary', method: 'GET' })
}

/** 删除当前用户的一次完整训练记录（会话、消息和评分）。 */
export function deleteChatSession(sessionId) {
  return request({
    url: `/chat/session/${sessionId}`,
    method: 'DELETE'
  })
}

/**
 * @api {POST} /api/chat/end 结束对话
 * @apiName EndChat
 * @apiGroup Chat
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} session_id 会话 ID
 *
 * @apiSuccess {Number} session_id 会话 ID
 * @apiSuccess {Boolean} ready_for_rating 是否已就绪评分
 */
export function endChat(sessionId) {
  return request({
    url: '/chat/end',
    method: 'POST',
    data: { session_id: sessionId }
  })
}
