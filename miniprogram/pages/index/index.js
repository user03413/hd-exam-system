// pages/index/index.js
Page({
  data: {
    // 页面数据
  },

  onLoad() {
    // 清除之前的用户数据
    const app = getApp()
    app.clearUserData()
  },

  // 跳转到学生端
  goToStudent() {
    wx.navigateTo({
      url: '/pages/student/login/login'
    })
  },

  // 跳转到教师端
  goToTeacher() {
    wx.navigateTo({
      url: '/pages/teacher/login/login'
    })
  }
})
