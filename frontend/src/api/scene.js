/**
 * =====================================================
 * 场景相关 API
 * 后端需实现：Python FastAPI
 * 路径前缀：/api/scene
 *
 * 已接入：场景列表与详情加载
 * =====================================================
 */

import request from './request'

/**
 * @api {GET} /api/scene/list 获取场景列表
 * @apiName GetSceneList
 * @apiGroup Scene
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiSuccess {Array} scenes 场景列表
 * @apiSuccess {Number} scenes.id 场景 ID
 * @apiSuccess {String} scenes.title 场景标题
 * @apiSuccess {String} scenes.description 场景描述
 * @apiSuccess {String} scenes.cover 场景封面图 URL
 * @apiSuccess {String} scenes.role 角色信息
 * @apiSuccess {Number} scenes.difficulty 难度等级 1-5
 *
 * @apiExample 前端调用：
 * const scenes = await getSceneList()
 * // scenes = [
 * //   { id: 1, title: '异物梗阻急救', description: '...', cover: '...', role: '成人患者', difficulty: 3 },
 * //   { id: 2, title: '第一次独立看病', description: '...', cover: '...', role: '青少年患者', difficulty: 2 }
 * // ]
 */
export function getSceneList() {
  return request({
    url: '/scene/list',
    method: 'GET'
  })
}

/**
 * @api {GET} /api/scene/:id 获取单个场景详情
 * @apiName GetSceneDetail
 * @apiGroup Scene
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {Number} id 场景 ID
 *
 * @apiSuccess {Object} scene 场景详情
 * @apiSuccess {Number} scene.id 场景 ID
 * @apiSuccess {String} scene.title 场景标题
 * @apiSuccess {String} scene.description 场景描述
 * @apiSuccess {String} scene.background 场景背景
 * @apiSuccess {String} scene.role 角色信息
 * @apiSuccess {String} scene.role_avatar 角色头像 URL
 * @apiSuccess {String} scene.opening_message 角色开场白
 * @apiSuccess {Object} scene.config 场景配置
 */
export function getSceneDetail(id) {
  return request({
    url: `/scene/${id}`,
    method: 'GET'
  })
}
