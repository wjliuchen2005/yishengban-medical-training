/**
 * =====================================================
 * 认证相关 API
 * 后端需实现：Python FastAPI
 * 路径前缀：/api/auth
 * =====================================================
 */

import request from './request'

/**
 * @api {POST} /api/auth/register 用户注册
 * @apiName Register
 * @apiGroup Auth
 *
 * @apiParam {String} username 用户名（3-20字符）
 * @apiParam {String} password 密码（6-20字符）
 * @apiParam {String} [real_name] 真实姓名
 * @apiParam {String} [student_id] 学号
 * @apiParam {String} [email] 邮箱
 *
 * @apiSuccess {String} token JWT token
 * @apiSuccess {Object} user 用户信息
 *
 * @apiExample 前端调用：
 * const res = await register({ username: 'test', password: '123456' })
 */
export function register(data) {
  return request({
    url: '/auth/register',
    method: 'POST',
    data
  })
}

/**
 * @api {POST} /api/auth/login 用户登录
 * @apiName Login
 * @apiGroup Auth
 *
 * @apiParam {String} username 用户名
 * @apiParam {String} password 密码
 *
 * @apiSuccess {String} token JWT token
 * @apiSuccess {Object} user 用户信息（id, username, real_name, student_id, school, email, phone, avatar_url）
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data
  })
}

/**
 * @api {POST} /api/auth/logout 退出登录
 * @apiName Logout
 * @apiGroup Auth
 *
 * @apiSuccess {Boolean} success 是否成功
 */
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'POST'
  })
}

/**
 * @api {GET} /api/auth/me 获取当前登录用户信息
 * @apiName GetCurrentUser
 * @apiGroup Auth
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiSuccess {Object} user 用户信息
 */
export function getProfile() {
  return request({
    url: '/auth/me',
    method: 'GET'
  })
}