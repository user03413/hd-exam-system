/**
 * pages/student/exam/exam.js - 考试答题页
 */

const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    chapter: '',
    questions: [],
    answers: {},
    total: 0,
    answered: 0,
    progress: 0,
    timerText: '00:00',
    seconds: 0,
    timer: null
  },

  /**
   * 页面加载
   */
  onLoad() {
    console.log('[Exam] 页面加载')
    
    // 检查登录状态
    if (!this.checkLogin()) {
      return
    }
    
    // 显示章节信息
    this.showChapterInfo()
    
    // 开始考试
    this.startExam()
  },

  /**
   * 页面卸载
   */
  onUnload() {
    // 清除计时器
    if (this.data.timer) {
      clearInterval(this.data.timer)
    }
  },

  /**
   * 检查登录状态
   */
  checkLogin() {
    try {
      const app = getApp()
      if (!app || !app.globalData) {
        util.showError('请先登录')
        this.redirectToLogin()
        return false
      }
      
      if (!app.globalData.sessionId) {
        util.showError('请先登录')
        this.redirectToLogin()
        return false
      }
      
      return true
    } catch (err) {
      console.error('[Exam] 检查登录失败:', err)
      util.showError('请先登录')
      this.redirectToLogin()
      return false
    }
  },

  /**
   * 跳转到登录页
   */
  redirectToLogin() {
    setTimeout(() => {
      wx.redirectTo({
        url: '/pages/student/login/login'
      })
    }, 1500)
  },

  /**
   * 显示章节信息
   */
  showChapterInfo() {
    try {
      const app = getApp()
      if (app && app.globalData && app.globalData.chapter) {
        const chapter = app.globalData.chapter
        this.setData({ chapter })
        wx.setNavigationBarTitle({
          title: chapter + ' - 答题中'
        })
      }
    } catch (err) {
      console.error('[Exam] 显示章节失败:', err)
    }
  },

  /**
   * 获取会话ID
   */
  getSessionId() {
    try {
      const app = getApp()
      return app && app.globalData ? app.globalData.sessionId : null
    } catch (err) {
      console.error('[Exam] 获取sessionId失败:', err)
      return null
    }
  },

  /**
   * 开始考试
   */
  async startExam() {
    const sessionId = this.getSessionId()
    
    if (!sessionId) {
      util.showError('会话已过期，请重新登录')
      this.redirectToLogin()
      return
    }
    
    util.showLoading('加载题目...')

    try {
      const res = await api.startExam(sessionId)
      console.log('[Exam] 开始考试结果:', res)
      
      if (res && res.success) {
        // 处理题目数据
        const questions = this.processQuestions(res.questions)
        
        this.setData({
          questions: questions,
          total: res.total || questions.length
        })

        // 保存题目到全局
        this.saveQuestions(questions)

        // 开始计时
        this.startTimer()

        util.hideLoading()
      } else {
        util.showError(res.message || '加载题目失败')
        util.hideLoading()
      }
    } catch (err) {
      console.error('[Exam] 加载题目失败:', err)
      util.showError('加载题目失败，请重试')
      util.hideLoading()
    }
  },

  /**
   * 处理题目数据
   */
  processQuestions(questions) {
    if (!questions || !Array.isArray(questions)) {
      return []
    }
    
    return questions.map(q => {
      return {
        ...q,
        typeClass: util.getTypeClass(q.type),
        diffClass: util.getDifficultyClass(q.difficulty)
      }
    })
  },

  /**
   * 保存题目到全局
   */
  saveQuestions(questions) {
    try {
      const app = getApp()
      if (app && app.globalData) {
        app.globalData.questions = questions
      }
    } catch (err) {
      console.error('[Exam] 保存题目失败:', err)
    }
  },

  /**
   * 开始计时
   */
  startTimer() {
    const timer = setInterval(() => {
      const seconds = this.data.seconds + 1
      this.setData({
        seconds: seconds,
        timerText: util.formatDuration(seconds)
      })
    }, 1000)

    this.setData({ timer: timer })
  },

  /**
   * 选择选项
   */
  selectOption(e) {
    const { seq, key, type } = e.currentTarget.dataset
    const answers = { ...this.data.answers }

    if (type === '单选题') {
      answers[seq] = key
    } else {
      // 多选处理
      if (!answers[seq]) {
        answers[seq] = []
      }
      
      const index = answers[seq].indexOf(key)
      if (index > -1) {
        answers[seq].splice(index, 1)
      } else {
        answers[seq].push(key)
      }
    }

    this.setData({ answers })
    this.updateProgress()
  },

  /**
   * 输入简答题
   */
  inputShortAnswer(e) {
    const { seq } = e.currentTarget.dataset
    const value = e.detail.value.trim()
    const answers = { ...this.data.answers }
    
    if (value) {
      answers[seq] = value
    } else {
      delete answers[seq]
    }

    this.setData({ answers })
    this.updateProgress()
  },

  /**
   * 更新进度
   */
  updateProgress() {
    const answered = Object.keys(this.data.answers).length
    const progress = this.data.total > 0 
      ? Math.round((answered / this.data.total) * 100) 
      : 0
    
    this.setData({
      answered: answered,
      progress: progress
    })
  },

  /**
   * 提交答卷
   */
  async handleSubmit() {
    const { questions, answers, total } = this.data

    // 检查是否完成所有题目
    if (Object.keys(answers).length < total) {
      const confirm = await util.showConfirm('还有题目未作答，确定提交吗？')
      if (!confirm) return
    }

    const sessionId = this.getSessionId()
    
    if (!sessionId) {
      util.showError('会话已过期，请重新登录')
      this.redirectToLogin()
      return
    }

    util.showLoading('提交中...')

    try {
      // 停止计时
      if (this.data.timer) {
        clearInterval(this.data.timer)
      }

      // 提交答案
      const res = await api.submitExam(sessionId, answers)
      console.log('[Exam] 提交结果:', res)

      if (res && res.success) {
        // 保存结果到全局
        this.saveResults(answers, res)

        util.hideLoading()
        util.showSuccess('提交成功！')

        // 跳转到成绩页
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/student/result/result'
          })
        }, 1000)
      } else {
        util.showError(res.message || '提交失败')
        util.hideLoading()
      }
    } catch (err) {
      console.error('[Exam] 提交失败:', err)
      util.showError('提交失败，请重试')
      util.hideLoading()
    }
  },

  /**
   * 保存结果到全局
   */
  saveResults(answers, res) {
    try {
      const app = getApp()
      if (app && app.globalData) {
        app.globalData.answers = answers
        app.globalData.results = res.results
        app.globalData.score = res.score
        app.globalData.duration_seconds = this.data.seconds
      }
    } catch (err) {
      console.error('[Exam] 保存结果失败:', err)
    }
  }
})
