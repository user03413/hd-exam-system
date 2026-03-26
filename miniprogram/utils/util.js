// utils/util.js - 工具函数

/**
 * 显示加载提示
 */
function showLoading(title = '加载中...') {
  wx.showLoading({
    title: title,
    mask: true
  })
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
  wx.hideLoading()
}

/**
 * 显示成功提示
 */
function showSuccess(title) {
  wx.showToast({
    title: title,
    icon: 'success',
    duration: 2000
  })
}

/**
 * 显示错误提示
 */
function showError(title) {
  wx.showToast({
    title: title,
    icon: 'none',
    duration: 2000
  })
}

/**
 * 显示确认对话框
 */
function showConfirm(content, title = '提示') {
  return new Promise((resolve, reject) => {
    wx.showModal({
      title: title,
      content: content,
      success: (res) => {
        if (res.confirm) {
          resolve(true)
        } else {
          resolve(false)
        }
      },
      fail: reject
    })
  })
}

/**
 * 复制文本到剪贴板
 */
function copyToClipboard(text) {
  return new Promise((resolve, reject) => {
    wx.setClipboardData({
      data: text,
      success: () => {
        showSuccess('已复制')
        resolve()
      },
      fail: reject
    })
  })
}

/**
 * 格式化时间
 */
function formatTime(date) {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('-')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

function formatNumber(n) {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

/**
 * 格式化时长（秒转分:秒）
 */
function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${formatNumber(minutes)}:${formatNumber(secs)}`
}

/**
 * 获取题型样式类
 */
function getTypeClass(type) {
  const typeMap = {
    '单选题': 'type-single',
    '多选题': 'type-multiple',
    '简答题': 'type-short'
  }
  return typeMap[type] || ''
}

/**
 * 获取难度样式类
 */
function getDifficultyClass(difficulty) {
  const diffMap = {
    '基础': 'diff-easy',
    '中等': 'diff-medium',
    '困难': 'diff-hard'
  }
  return diffMap[difficulty] || 'diff-medium'
}

/**
 * 计算分数
 */
function calculateScore(results) {
  let total = 0
  let correct = 0
  let partial = 0
  let wrong = 0

  results.forEach(item => {
    total += 10
    if (item.is_correct) {
      correct++
    } else if (item.score > 0) {
      partial++
    } else {
      wrong++
    }
  })

  return {
    total,
    correct,
    partial,
    wrong
  }
}

/**
 * 获取分数评价
 */
function getScoreComment(score) {
  if (score >= 90) return '优秀！继续保持！'
  if (score >= 80) return '良好，再接再厉！'
  if (score >= 60) return '及格，需加强学习。'
  return '不及格，请认真复习。'
}

module.exports = {
  showLoading,
  hideLoading,
  showSuccess,
  showError,
  showConfirm,
  copyToClipboard,
  formatTime,
  formatDuration,
  getTypeClass,
  getDifficultyClass,
  calculateScore,
  getScoreComment
}
