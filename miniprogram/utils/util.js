/**
 * utils/util.js - 工具函数
 */

/**
 * 显示加载提示
 * @param {string} title - 提示文字
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
  try {
    wx.hideLoading()
  } catch (err) {
    // ignore
  }
}

/**
 * 显示成功提示
 * @param {string} title - 提示文字
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
 * @param {string} title - 提示文字
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
 * @param {string} content - 内容
 * @param {string} title - 标题
 * @returns {Promise<boolean>}
 */
function showConfirm(content, title = '提示') {
  return new Promise((resolve) => {
    wx.showModal({
      title: title,
      content: content,
      success: (res) => {
        resolve(res.confirm)
      },
      fail: () => {
        resolve(false)
      }
    })
  })
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise}
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
 * @param {Date} date - 日期对象
 * @returns {string}
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

/**
 * 格式化数字（补零）
 * @param {number} n - 数字
 * @returns {string}
 */
function formatNumber(n) {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

/**
 * 格式化时长（秒转 MM:SS）
 * @param {number} seconds - 秒数
 * @returns {string}
 */
function formatDuration(seconds) {
  if (typeof seconds !== 'number' || isNaN(seconds)) {
    return '00:00'
  }
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${formatNumber(minutes)}:${formatNumber(secs)}`
}

/**
 * 获取题型样式类
 * @param {string} type - 题型
 * @returns {string}
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
 * @param {string} difficulty - 难度
 * @returns {string}
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
 * 计算分数统计
 * @param {Array} results - 结果数组
 * @returns {Object}
 */
function calculateScore(results) {
  if (!results || !Array.isArray(results)) {
    return { total: 0, correct: 0, partial: 0, wrong: 0 }
  }
  
  let correct = 0
  let partial = 0
  let wrong = 0

  results.forEach(item => {
    if (item.is_correct) {
      correct++
    } else if (item.score > 0) {
      partial++
    } else {
      wrong++
    }
  })

  return {
    total: results.length * 10,
    correct,
    partial,
    wrong
  }
}

/**
 * 获取分数评价
 * @param {number} score - 分数
 * @returns {string}
 */
function getScoreComment(score) {
  if (typeof score !== 'number' || isNaN(score)) {
    return '未知'
  }
  if (score >= 90) return '优秀！继续保持！'
  if (score >= 80) return '良好，再接再厉！'
  if (score >= 60) return '及格，需加强学习。'
  return '不及格，请认真复习。'
}

// 导出模块
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
