// pages/student/exam/exam.js
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

  onLoad() {
    const app = getApp()
    
    // 检查是否已登录
    if (!app.globalData.sessionId) {
      util.showError('请先登录')
      setTimeout(() => {
        wx.redirectTo({
          url: '/pages/student/login/login'
        })
      }, 1500)
      return
    }

    // 显示章节信息
    if (app.globalData.chapter) {
      this.setData({
        chapter: app.globalData.chapter
      })
      wx.setNavigationBarTitle({
        title: app.globalData.chapter + ' - 答题中'
      })
    }

    // 开始考试
    this.startExam()
  },

  onUnload() {
    // 清除计时器
    if (this.data.timer) {
      clearInterval(this.data.timer)
    }
  },

  // 开始考试
  async startExam() {
    const app = getApp()
    
    util.showLoading('加载题目...')

    try {
      const res = await api.startExam(app.globalData.sessionId)
      
      if (res.success) {
        // 处理题目数据
        const questions = res.questions.map(q => {
          // 转换选项为列表格式
          const optionsList = {}
          if (q.options) {
            Object.entries(q.options).forEach(([key, value]) => {
              optionsList[key] = value
            })
          }

          return {
            ...q,
            optionsList: optionsList,
            typeClass: util.getTypeClass(q.type),
            diffClass: util.getDifficultyClass(q.difficulty)
          }
        })

        this.setData({
          questions: questions,
          total: res.total
        })

        // 保存题目到全局
        app.globalData.questions = questions

        // 开始计时
        this.startTimer()

        util.hideLoading()
      } else {
        util.showError(res.message || '加载题目失败')
        util.hideLoading()
      }
    } catch (err) {
      console.error('加载题目失败:', err)
      util.showError('加载题目失败，请重试')
      util.hideLoading()
    }
  },

  // 开始计时
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

  // 选择选项
  selectOption(e) {
    const { seq, key, type } = e.currentTarget.dataset
    const answers = { ...this.data.answers }

    if (type === '单选题') {
      // 单选：直接赋值
      answers[seq] = key
    } else {
      // 多选：数组处理
      if (!answers[seq]) {
        answers[seq] = []
      }
      
      const index = answers[seq].indexOf(key)
      if (index > -1) {
        // 已选中，取消选择
        answers[seq].splice(index, 1)
      } else {
        // 未选中，添加
        answers[seq].push(key)
      }
    }

    this.setData({ answers })
    this.updateProgress()
  },

  // 输入简答题
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

  // 更新进度
  updateProgress() {
    const answered = Object.keys(this.data.answers).length
    const progress = (answered / this.data.total) * 100
    
    this.setData({
      answered: answered,
      progress: progress
    })
  },

  // 提交答卷
  async handleSubmit() {
    const { questions, answers, total } = this.data

    // 检查是否完成所有题目
    if (Object.keys(answers).length < total) {
      const confirm = await util.showConfirm('还有题目未作答，确定提交吗？')
      if (!confirm) return
    }

    util.showLoading('提交中...')

    try {
      const app = getApp()
      
      // 停止计时
      if (this.data.timer) {
        clearInterval(this.data.timer)
      }

      // 提交答案
      const res = await api.submitExam(app.globalData.sessionId, answers)

      if (res.success) {
        // 保存结果到全局
        app.globalData.answers = answers
        app.globalData.results = res.results
        app.globalData.score = res.score

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
      console.error('提交失败:', err)
      util.showError('提交失败，请重试')
      util.hideLoading()
    }
  }
})
