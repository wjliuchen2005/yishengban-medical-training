/**
 * =====================================================
 * 评分相关 API
 * 后端需实现：Python FastAPI
 * 路径前缀：/api/result
 *
 * 已接入：三维评分、路径对比、对话回放与站内分享链接
 * =====================================================
 */

import request from './request'

/**
 * @api {GET} /api/result/:sessionId 获取会话评分结果
 * @apiName GetResult
 * @apiGroup Result
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} session_id 会话 ID
 *
 * @apiSuccess {Number} total_score 总分（0-100）
 * @apiSuccess {Object} dimensions 三维度评分
 * @apiSuccess {Number} dimensions.accuracy 医学准确性（0-100）
 * @apiSuccess {Number} dimensions.warmth 沟通温度（0-100）
 * @apiSuccess {Number} dimensions.decision 决策合理性（0-100）
 * @apiSuccess {Array} messages 对话回放（带标注）
 * @apiSuccess {Object} messages.issue_points 错误点
 * @apiSuccess {Object} messages.good_points 正确点
 * @apiSuccess {Object} decision_tree 决策树可视化数据
 * @apiSuccess {String} decision_tree.nodes 节点
 * @apiSuccess {String} decision_tree.edges 边
 * @apiSuccess {String} share_url 站内分享链接
 */
export function getResult(sessionId) {
  return request({
    url: `/result/${sessionId}`,
    method: 'GET'
  })
}

/**
 * @api {POST} /api/result/:sessionId/share 生成分享链接
 * @apiName ShareResult
 * @apiGroup Result
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} session_id 会话 ID
 *
 * @apiSuccess {String} share_url 分享链接
 *
 */
export function shareResult(sessionId) {
  return request({
    url: `/result/${sessionId}/share`,
    method: 'POST'
  })
}
