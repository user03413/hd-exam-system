/**
 * utils/request.js - API请求封装
 * 
 * 官方规范要点：
 * 1. 不能在模块顶层调用 getApp()，因为模块加载时 App 可能未初始化
 * 2. 应在函数内部调用 getApp()
 * 3. 开发环境需在开发者工具中关闭域名校验
 */

// API基础地址（与 app.js 保持一致）
const DEFAULT_BASE_URL = 'https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site'

/**
 * 获取API基础地址
 * 优先使用 globalData 中的配置，否则使用默认值
 */
function getBaseUrl() {
  try {
    const app = getApp()
    if (app && app.globalData && app.globalData.baseUrl) {
      return app.globalData.baseUrl
    }
  } catch (err) {
    console.warn('[Request] 获取 globalData.baseUrl 失败，使用默认值')
  }
  return DEFAULT_BASE_URL
}

/**
 * 发送网络请求
 * @param {string} url - 请求路径（不含基础地址）
 * @param {string} method - 请求方法 GET/POST
 * @param {object} data - 请求数据
 * @param {number} timeout - 超时时间（毫秒）
 */
function request(url, method = 'GET', data = {}, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const baseUrl = getBaseUrl()
    const fullUrl = baseUrl + url
    
    console.log('[Request]', method, fullUrl, data)
    
    wx.request({
      url: fullUrl,
      method: method,
      data: data,
      header: {
        'content-type': 'application/json'
      },
      timeout: timeout,
      success: (res) => {
        console.log('[Response]', res.statusCode, res.data)
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          const error = new Error(`请求失败: HTTP ${res.statusCode}`)
          error.statusCode = res.statusCode
          error.data = res.data
          reject(error)
        }
      },
      fail: (err) => {
        console.error('[Request Error]', err)
        const error = new Error(err.errMsg || '网络请求失败')
        error.errMsg = err.errMsg
        reject(error)
      }
    })
  })
}

/**
 * 学生登录验证
 * @param {string} studentId - 学号
 * @param {string} chapter - 章节名称（可选）
 */
function verifyStudent(studentId, chapter = '') {
  return request('/api/exam/verify', 'POST', {
    student_id: studentId,
    chapter: chapter
  })
}

/**
 * 开始考试
 * @param {string} sessionId - 会话ID
 */
function startExam(sessionId) {
  return request('/api/exam/start', 'POST', {
    session_id: sessionId
  })
}

/**
 * 提交答案
 * @param {string} sessionId - 会话ID
 * @param {object} answers - 答案对象
 */
function submitExam(sessionId, answers) {
  return request('/api/exam/submit', 'POST', {
    session_id: sessionId,
    answers: answers
  })
}

/**
 * 获取拓展内容
 * @param {string} question - 问题内容
 * @param {string} chapter - 章节名称
 */
function getExtension(question, chapter) {
  return request('/api/exam/extension', 'POST', {
    question: question,
    chapter: chapter
  })
}

/**
 * 导出报告
 * @param {string} sessionId - 会话ID
 * @param {array} extensions - 拓展内容列表
 */
function exportReport(sessionId, extensions) {
  return request('/api/exam/export', 'POST', {
    session_id: sessionId,
    extensions: extensions
  })
}

/**
 * 教师登录
 * @param {string} teacherId - 教师工号
 */
function teacherLogin(teacherId) {
  return request('/api/exam/teacher/login', 'POST', {
    teacher_id: teacherId
  })
}

/**
 * 获取教师统计数据
 */
function getTeacherStats() {
  return request('/api/exam/teacher/stats', 'GET')
}

/**
 * 获取章节列表
 */
function getChapters() {
  return request('/api/exam/chapters', 'GET')
}

/**
 * 生成章节链接
 * @param {string} chapter - 章节名称（空表示全题库）
 */
function generateChapterLink(chapter) {
  const url = chapter 
    ? `/api/exam/chapter-link?chapter=${encodeURIComponent(chapter)}`
    : '/api/exam/chapter-link'
  return request(url, 'GET')
}

// 导出模块
module.exports = {
  request,
  verifyStudent,
  startExam,
  submitExam,
  getExtension,
  exportReport,
  teacherLogin,
  getTeacherStats,
  getChapters,
  generateChapterLink
}
