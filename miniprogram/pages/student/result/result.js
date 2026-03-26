/**
 * pages/student/result/result.js - 考试结果页
 */

const util = require('../../../utils/util')

Page({
  data: {
    score: 0,
    comment: '',
    stats: {
      correct: 0,
      partial: 0,
      wrong: 0
    },
    duration: '',
    results: []
  },

  /**
   * 页面加载
   */
  onLoad() {
    console.log('[Result] 页面加载')
    
    // 检查是否有结果数据
    if (!this.checkResults()) {
      return
    }
    
    // 显示结果
    this.showResults()
    
    // 设置页面标题
    wx.setNavigationBarTitle({
      title: '考试成绩'
    })
  },

  /**
   * 检查结果数据
   */
  checkResults() {
    try {
      const app = getApp()
      if (!app || !app.globalData) {
        util.showError('未找到考试结果')
        this.redirectToIndex()
        return false
      }
      
      if (!app.globalData.results || !Array.isArray(app.globalData.results)) {
        util.showError('未找到考试结果')
        this.redirectToIndex()
        return false
      }
      
      return true
    } catch (err) {
      console.error('[Result] 检查结果失败:', err)
      util.showError('未找到考试结果')
      this.redirectToIndex()
      return false
    }
  },

  /**
   * 跳转到首页
   */
  redirectToIndex() {
    setTimeout(() => {
      wx.redirectTo({
        url: '/pages/index/index'
      })
    }, 1500)
  },

  /**
   * 获取全局数据
   */
  getGlobalData() {
    try {
      const app = getApp()
      return app && app.globalData ? app.globalData : null
    } catch (err) {
      console.error('[Result] 获取全局数据失败:', err)
      return null
    }
  },

  /**
   * 显示结果
   */
  showResults() {
    const globalData = this.getGlobalData()
    if (!globalData) {
      return
    }
    
    // 处理结果数据
    const results = this.processResults(globalData.results)
    
    // 计算统计数据
    const stats = util.calculateScore(globalData.results)
    
    // 获取评价
    const score = globalData.score || 0
    const comment = util.getScoreComment(score)
    
    // 格式化时长
    const duration = util.formatDuration(globalData.duration_seconds || 0)

    this.setData({
      score: score,
      comment: comment,
      stats: stats,
      duration: duration,
      results: results
    })
  },

  /**
   * 处理结果数据
   */
  processResults(results) {
    if (!results || !Array.isArray(results)) {
      return []
    }
    
    return results.map(r => {
      // 处理用户答案显示
      let user_answer_display = ''
      if (r.type === '简答题') {
        user_answer_display = r.user_answer || '未作答'
      } else {
        user_answer_display = Array.isArray(r.user_answer) 
          ? r.user_answer.join('') 
          : (r.user_answer || '未作答')
      }

      return {
        ...r,
        user_answer_display: user_answer_display,
        typeClass: util.getTypeClass(r.type)
      }
    })
  },

  /**
   * 重新开始
   */
  handleRestart() {
    // 清除用户数据
    try {
      const app = getApp()
      if (app && typeof app.clearUserData === 'function') {
        app.clearUserData()
      }
    } catch (err) {
      console.error('[Result] 清除数据失败:', err)
    }
    
    // 跳转到首页
    wx.redirectTo({
      url: '/pages/index/index'
    })
  }
})
