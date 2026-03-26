/**
 * pages/teacher/login/login.js - 教师登录页
 */

const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    teacherId: '',
    loading: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('[TeacherLogin] 页面加载', options)
  },

  /**
   * 输入教师工号
   */
  onInputTeacherId(e) {
    this.setData({
      teacherId: e.detail.value.trim()
    })
  },

  /**
   * 登录
   */
  async handleLogin() {
    const { teacherId } = this.data

    // 验证输入
    if (!teacherId) {
      util.showError('请输入教师工号')
      return
    }

    // 防止重复提交
    if (this.data.loading) {
      return
    }

    this.setData({ loading: true })
    util.showLoading('登录中...')

    try {
      const res = await api.teacherLogin(teacherId)
      console.log('[TeacherLogin] 登录结果:', res)
      
      if (res && res.success && res.teacher && res.teacher.is_teacher) {
        // 保存教师信息到全局
        const app = getApp()
        if (app && app.globalData) {
          app.globalData.userInfo = res.teacher
        }

        util.showSuccess('登录成功')
        
        // 延迟跳转
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/teacher/stats/stats'
          })
        }, 1000)
      } else {
        util.showError('教师工号错误或权限不足')
      }
    } catch (err) {
      console.error('[TeacherLogin] 登录失败:', err)
      util.showError('登录失败，请重试')
    } finally {
      this.setData({ loading: false })
      util.hideLoading()
    }
  }
})
