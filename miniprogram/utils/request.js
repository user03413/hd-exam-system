// utils/request.js - API请求封装

/**
 * 获取API基础地址
 */
function getBaseUrl() {
  const app = getApp()
  if (app && app.globalData) {
    return app.globalData.baseUrl
  }
  // 默认值
  return 'https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site'
}

/**
 * 发送请求
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const baseUrl = getBaseUrl()
    const fullUrl = baseUrl + url
    
    wx.request({
      url: fullUrl,
      method: method,
      data: data,
      header: {
        'content-type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

/**
 * 学生登录验证
 */
function verifyStudent(studentId, chapter = '') {
  return request('/api/exam/verify', 'POST', {
    student_id: studentId,
    chapter: chapter
  })
}

/**
 * 开始考试
 */
function startExam(sessionId) {
  return request('/api/exam/start', 'POST', {
    session_id: sessionId
  })
}

/**
 * 提交答案
 */
function submitExam(sessionId, answers) {
  return request('/api/exam/submit', 'POST', {
    session_id: sessionId,
    answers: answers
  })
}

/**
 * 获取拓展内容
 */
function getExtension(question, chapter) {
  return request('/api/exam/extension', 'POST', {
    question: question,
    chapter: chapter
  })
}

/**
 * 导出报告
 */
function exportReport(sessionId, extensions) {
  return request('/api/exam/export', 'POST', {
    session_id: sessionId,
    extensions: extensions
  })
}

/**
 * 教师登录
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
 */
function generateChapterLink(chapter) {
  const url = chapter 
    ? `/api/exam/chapter-link?chapter=${encodeURIComponent(chapter)}`
    : '/api/exam/chapter-link'
  return request(url, 'GET')
}

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
