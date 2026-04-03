/**
 * pages/teacher/stats/stats.js - 教师统计页
 */

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
    records: [],
    loading: false
  },

  /**
   * 页面加载
   */
  onLoad() {
    console.log('[Stats] 页面加载')
    this.loadStats()
  },

  /**
   * 页面显示
   */
  onShow() {
    // 每次显示时刷新数据
    this.loadStats()
  },

  /**
   * 加载统计数据
   */
  async loadStats() {
    if (this.data.loading) {
      return
    }
    
    this.setData({ loading: true })

    try {
      const res = await api.getTeacherStats()
      console.log('[Stats] 统计数据:', res)
      
      if (res && res.success) {
        this.setData({
          stats: res.stats || this.data.stats,
          records: res.records || []
        })
      }
    } catch (err) {
      console.error('[Stats] 加载统计数据失败:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  /**
   * 跳转到章节出题
   */
  goToChapter() {
    wx.navigateTo({
      url: '/pages/teacher/chapter/chapter'
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadStats().then(() => {
      wx.stopPullDownRefresh()
    })
  }
})
