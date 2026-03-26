/**
 * pages/student/login/login.js - 学生登录页
 */

const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: '',
    chapter: '',
    loading: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('[StudentLogin] 页面加载', options)
    
    // 从URL参数中获取章节信息
    if (options && options.chapter) {
      const chapter = decodeURIComponent(options.chapter)
      this.setData({ chapter })
      
      // 更新页面标题
      wx.setNavigationBarTitle({
        title: chapter + ' - 考试'
      })
    }
  },

  /**
   * 输入学号
   */
  onInputStudentId(e) {
    this.setData({
      studentId: e.detail.value.trim()
    })
  },

  /**
   * 登录验证
   */
  async handleLogin() {
    const { studentId, chapter } = this.data

    // 验证输入
    if (!studentId) {
      util.showError('请输入学号')
      return
    }

    // 防止重复提交
    if (this.data.loading) {
      return
    }

    this.setData({ loading: true })
    util.showLoading('验证中...')

    try {
      const res = await api.verifyStudent(studentId, chapter)
      console.log('[StudentLogin] 验证结果:', res)
      
      if (res && res.success) {
        // 检查是否是教师账号
        if (res.student && res.student.is_teacher) {
          util.showError('教师账号请使用教师端登录')
          return
        }

        // 保存用户信息到全局
        const app = getApp()
        if (app && app.globalData) {
          app.globalData.userInfo = res.student
          app.globalData.sessionId = res.session_id
          app.globalData.chapter = res.chapter || chapter
        }

        // 保存sessionId到本地存储
        try {
          wx.setStorageSync('sessionId', res.session_id)
        } catch (e) {
          console.error('[StudentLogin] 保存sessionId失败:', e)
        }

        util.showSuccess(res.message || '验证成功')
        
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
      console.error('[StudentLogin] 登录失败:', err)
      util.showError('登录失败，请重试')
    } finally {
      this.setData({ loading: false })
      util.hideLoading()
    }
  }
})
