// pages/teacher/chapter/chapter.js
const api = require('../../../utils/request')
const util = require('../../../utils/util')

Page({
  data: {
    chapters: [],
    selectedChapter: '',
    selectedCount: 0,
    examLink: '',
    loading: false
  },

  onLoad() {
    this.loadChapters()
  },

  // 加载章节列表
  async loadChapters() {
    try {
      util.showLoading('加载章节...')
      
      const res = await api.getChapters()
      
      if (res.success && res.chapters) {
        // 添加"全题库"选项
        const chapters = [
          { chapter: '全题库', count: 244 },
          ...res.chapters
        ]
        
        this.setData({
          chapters: chapters
        })
      }
      
      util.hideLoading()
    } catch (err) {
      console.error('加载章节失败:', err)
      util.showError('加载章节失败')
      util.hideLoading()
    }
  },

  // 选择章节
  onChapterChange(e) {
    const index = e.detail.value
    const chapter = this.data.chapters[index]
    
    this.setData({
      selectedChapter: chapter.chapter,
      selectedCount: chapter.count,
      examLink: '' // 清空之前的链接
    })
  },

  // 生成链接
  async generateLink() {
    const { selectedChapter } = this.data

    if (!selectedChapter) {
      util.showError('请先选择章节')
      return
    }

    this.setData({ loading: true })
    util.showLoading('生成链接...')

    try {
      const chapter = selectedChapter === '全题库' ? '' : selectedChapter
      const res = await api.generateChapterLink(chapter)
      
      if (res.success) {
        this.setData({
          examLink: res.link
        })
        util.showSuccess('链接生成成功')
      } else {
        util.showError(res.message || '生成链接失败')
      }
    } catch (err) {
      console.error('生成链接失败:', err)
      util.showError('生成链接失败')
    } finally {
      this.setData({ loading: false })
      util.hideLoading()
    }
  },

  // 复制链接
  async copyLink() {
    const { examLink } = this.data
    
    if (!examLink) {
      util.showError('暂无链接')
      return
    }

    try {
      await util.copyToClipboard(examLink)
    } catch (err) {
      console.error('复制失败:', err)
      util.showError('复制失败')
    }
  }
})
