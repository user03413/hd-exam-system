// pages/teacher/stats/stats.js
const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    stats: {
      total_students: 70,
      total_exams: 0,
      avg_score: 0,
      pass_rate: 0
    },
    records: []
  },

  onLoad() {
    this.loadStats()
  },

  // 加载统计数据
  async loadStats() {
    try {
      const res = await api.getTeacherStats()
      
      if (res.success) {
        this.setData({
          stats: res.stats || this.data.stats,
          records: res.records || []
        })
      }
    } catch (err) {
      console.error('加载统计数据失败:', err)
    }
  },

  // 跳转到章节出题
  goToChapter() {
    wx.navigateTo({
      url: '/pages/teacher/chapter/chapter'
    })
  }
})
