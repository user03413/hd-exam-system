/**
 * app.js - 小程序入口文件
 * 
 * 官方规范要点：
 * 1. App() 必须在 app.js 中调用，且只能调用一次
 * 2. globalData 必须在 App() 的参数对象中定义
 * 3. 自定义方法可通过 this 访问
 */

// API基础地址配置
const API_BASE_URL = 'https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site'

App({
  /**
   * 全局数据 - 所有页面可通过 getApp().globalData 访问
   */
  globalData: {
    // API配置
    baseUrl: API_BASE_URL,
    
    // 用户信息
    userInfo: null,
    sessionId: null,
    chapter: null,
    
    // 考试数据
    questions: [],
    answers: {},
    results: null,
    score: 0,
    duration_seconds: 0,
    startTime: '',
    endTime: ''
  },

  /**
   * 小程序初始化完成时触发（全局只触发一次）
   */
  onLaunch(options) {
    console.log('[App] 小程序启动', options)
    
    // 恢复登录状态
    this.restoreSession()
  },

  /**
   * 小程序启动或从后台进入前台显示时触发
   */
  onShow(options) {
    console.log('[App] 小程序显示', options)
  },

  /**
   * 小程序从前台进入后台时触发
   */
  onHide() {
    console.log('[App] 小程序隐藏')
  },

  /**
   * 恢复会话状态
   */
  restoreSession() {
    try {
      const sessionId = wx.getStorageSync('sessionId')
      if (sessionId) {
        this.globalData.sessionId = sessionId
        console.log('[App] 恢复会话:', sessionId)
      }
    } catch (err) {
      console.error('[App] 恢复会话失败:', err)
    }
  },

  /**
   * 清除用户数据
   */
  clearUserData() {
    console.log('[App] 清除用户数据')
    
    this.globalData.userInfo = null
    this.globalData.sessionId = null
    this.globalData.chapter = null
    this.globalData.questions = []
    this.globalData.answers = {}
    this.globalData.results = null
    this.globalData.score = 0
    this.globalData.duration_seconds = 0
    this.globalData.startTime = ''
    this.globalData.endTime = ''
    
    try {
      wx.removeStorageSync('sessionId')
    } catch (err) {
      console.error('[App] 清除存储失败:', err)
    }
  },

  /**
   * 设置用户信息
   */
  setUserInfo(userInfo) {
    this.globalData.userInfo = userInfo
  },

  /**
   * 设置会话ID
   */
  setSessionId(sessionId) {
    this.globalData.sessionId = sessionId
    try {
      wx.setStorageSync('sessionId', sessionId)
    } catch (err) {
      console.error('[App] 保存会话失败:', err)
    }
  },

  /**
   * 获取会话ID
   */
  getSessionId() {
    return this.globalData.sessionId
  }
})
