// pages/student/result/result.js
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
    startTime: '',
    endTime: '',
    results: []
  },

  onLoad() {
    const app = getApp()
    
    // 检查是否有结果数据
    if (!app || !app.globalData || !app.globalData.results) {
      util.showError('未找到考试结果')
      setTimeout(() => {
        wx.redirectTo({
          url: '/pages/index/index'
        })
      }, 1500)
      return
    }

    // 处理结果数据
    const results = app.globalData.results.map(r => {
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

    // 计算统计数据
    const stats = util.calculateScore(app.globalData.results)

    // 获取评价
    const score = app.globalData.score || 0
    const comment = util.getScoreComment(score)

    this.setData({
      score: score,
      comment: comment,
      stats: stats,
      duration: util.formatDuration(app.globalData.duration_seconds || 0),
      startTime: app.globalData.startTime || '--',
      endTime: app.globalData.endTime || '--',
      results: results
    })

    // 设置页面标题
    wx.setNavigationBarTitle({
      title: '考试成绩'
    })
  },

  // 重新开始
  handleRestart() {
    const app = getApp()
    if (app && app.clearUserData) {
      app.clearUserData()
    }
    
    wx.redirectTo({
      url: '/pages/index/index'
    })
  }
})
