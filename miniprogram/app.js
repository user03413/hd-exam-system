// app.js
App({
  globalData: {
    // API基础地址
    baseUrl: 'https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site',
    // apiUrl: 'https://hd-exam-api.771794850.workers.dev', // Cloudflare API备用地址
    
    // 用户信息
    userInfo: null,
    sessionId: null,
    chapter: null,
    
    // 考试数据
    questions: [],
    answers: {},
    results: null
  },

  onLaunch() {
    // 检查登录状态
    const sessionId = wx.getStorageSync('sessionId')
    if (sessionId) {
      this.globalData.sessionId = sessionId
    }
  },

  // 清除用户数据
  clearUserData() {
    this.globalData.userInfo = null
    this.globalData.sessionId = null
    this.globalData.chapter = null
    this.globalData.questions = []
    this.globalData.answers = {}
    this.globalData.results = null
    wx.removeStorageSync('sessionId')
  }
})
