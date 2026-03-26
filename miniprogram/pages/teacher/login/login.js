// pages/teacher/login/login.js
const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    teacherId: '',
    loading: false
  },

  // 输入教师工号
  onInputTeacherId(e) {
    this.setData({
      teacherId: e.detail.value
    })
  },

  // 登录
  async handleLogin() {
    const { teacherId } = this.data

    if (!teacherId) {
      util.showError('请输入教师工号')
      return
    }

    this.setData({ loading: true })
    util.showLoading('登录中...')

    try {
      const res = await api.teacherLogin(teacherId)
      
      if (res.success && res.teacher && res.teacher.is_teacher) {
        // 保存教师信息
        const app = getApp()
        app.globalData.userInfo = res.teacher

        util.showSuccess('登录成功')
        
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/teacher/stats/stats'
          })
        }, 1000)
      } else {
        util.showError('教师工号错误或权限不足')
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
