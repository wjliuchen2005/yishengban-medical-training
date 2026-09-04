/**
 * =====================================================
 * 用户信息相关 API
 * 后端需实现：Python FastAPI
 * 路径前缀：/api/user
 * =====================================================
 */

import request from './request'

/**
 * @api {GET} /api/user/profile 获取当前用户信息
 * @apiName GetUserProfile
 * @apiGroup User
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiSuccess {Object} user 用户信息
 */
export function getUserProfile() {
  return request({
    url: '/user/profile',
    method: 'GET'
  })
}

/**
 * @api {PUT} /api/user/profile 修改用户信息（不含密码）
 * @apiName UpdateUserProfile
 * @apiGroup User
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {String} [real_name] 真实姓名
 * @apiParam {String} [student_id] 学号
 * @apiParam {String} [school] 学校
 * @apiParam {String} [email] 邮箱
 * @apiParam {String} [phone] 手机号
 * @apiParam {String} [avatar_url] 头像 URL
 *
 * @apiSuccess {Object} user 更新后的用户信息
 */
export function updateUserProfile(data) {
  return request({
    url: '/user/profile',
    method: 'PUT',
    data
  })
}

/**
 * @api {PUT} /api/user/password 修改密码（需要原密码验证）
 * @apiName ChangePassword
 * @apiGroup User
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {String} old_password 原密码
 * @apiParam {String} new_password 新密码（6-20字符）
 *
 * @apiSuccess {Boolean} success 是否成功
 *
 * @apiError 400 原密码错误
 */
export function changePassword(data) {
  return request({
    url: '/user/password',
    method: 'PUT',
    data
  })
}

/**
 * @api {POST} /api/user/avatar 上传头像
 * @apiName UploadAvatar
 * @apiGroup User
 *
 * @apiHeader {String} Authorization Bearer token
 *
 * @apiParam {File} file 头像文件
 *
 * @apiSuccess {String} avatar_url 头像 URL
 */
export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/user/avatar',
    method: 'POST',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}