/**
 * pages/index/index.js - 首页
 * 
 * 官方规范要点：
 * 1. getApp() 应在 Page 生命周期函数内调用
 * 2. 需检查返回值是否存在
 */

Page({
  data: {
    // 页面数据
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('[Index] 页面加载', options)
    
    // 清除之前的用户数据
    this.clearUserData()
  },

  /**
   * 清除用户数据
   */
  clearUserData() {
    try {
      const app = getApp()
      if (app && typeof app.clearUserData === 'function') {
        app.clearUserData()
        console.log('[Index] 已清除用户数据')
      }
    } catch (err) {
      console.error('[Index] 清除用户数据失败:', err)
    }
  },

  /**
   * 跳转到学生端
   */
  goToStudent() {
    wx.navigateTo({
      url: '/pages/student/login/login'
    })
  },

  /**
   * 跳转到教师端
   */
  goToTeacher() {
    wx.navigateTo({
      url: '/pages/teacher/login/login'
    })
  }
})
