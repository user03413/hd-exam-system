// pages/student/login/login.js
const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: '',
    chapter: '',
    loading: false
  },

  onLoad(options) {
    // 从URL参数中获取章节信息
    if (options.chapter) {
      this.setData({
        chapter: decodeURIComponent(options.chapter)
      })
      
      // 更新页面标题
      wx.setNavigationBarTitle({
        title: decodeURIComponent(options.chapter) + ' - 考试'
      })
    }
  },

  // 输入学号
  onInputStudentId(e) {
    this.setData({
      studentId: e.detail.value
    })
  },

  // 登录验证
  async handleLogin() {
    const { studentId, chapter } = this.data

    if (!studentId) {
      util.showError('请输入学号')
      return
    }

    this.setData({ loading: true })
    util.showLoading('验证中...')

    try {
      const res = await api.verifyStudent(studentId, chapter)
      
      if (res.success) {
        // 检查是否是教师账号
        if (res.student.is_teacher) {
          util.showError('教师账号请使用教师端登录')
          return
        }

        // 保存用户信息到全局
        const app = getApp()
        app.globalData.userInfo = res.student
        app.globalData.sessionId = res.session_id
        app.globalData.chapter = res.chapter || chapter

        // 保存sessionId到本地存储
        wx.setStorageSync('sessionId', res.session_id)

        util.showSuccess(res.message)
        
        // 延迟跳转，让用户看到成功提示
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/student/exam/exam'
          })
        }, 1000)
      } else {
        util.showError(res.message || '验证失败')
      }
    } catch (err) {
      console.error('登录失败:', err)
      util.showError('登录失败，请重试')
    } finally {
      this.setData({ loading: false })
      util.hideLoading()
    }
  }
})
