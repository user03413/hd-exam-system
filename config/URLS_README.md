# 火电机组考核系统 - 网址配置说明

> **最后更新**: 2024-03-30  
> **部署状态**: ✅ 已完成

---

## 📍 网址分类

### 一、Cloudflare 平台（主推）

| 名称 | 网址 | 状态 | 用途 |
|------|------|------|------|
| **Pages 前端** | https://hd-exam-system.pages.dev | ✅ 已部署 | 首页入口 |
| **学生考试** | https://hd-exam-system.pages.dev/exam | ✅ 已部署 | 学生在线答题 |
| **教师管理** | https://hd-exam-system.pages.dev/teacher | ✅ 已部署 | 教师后台管理 |
| **Workers API** | https://hd-exam-api.771794850.workers.dev | ✅ 运行中 | 后端 API |

---

### 二、Coze 平台（备用）

| 名称 | 网址 | 用途 |
|------|------|------|
| **统一入口** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/ | 首页入口 |
| **学生考试** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/exam | 学生答题 |
| **教师后台** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/teacher | 教师管理 |

---

### 三、GitHub 仓库

| 名称 | 网址 |
|------|------|
| **代码仓库** | https://github.com/user03413/hd-exam-system |

---

## 🔧 配置信息

### Cloudflare 配置

| 配置项 | 值 |
|--------|-----|
| Account ID | `57d6cde2e053b14fd28bd963ddb0975b` |
| Worker 名称 | `hd-exam-api` |
| Pages 项目 | `hd-exam-system` |
| D1 数据库 ID | `0cc8b804-1e56-4563-9b8d-f45a76370192` |

### 数据库状态

| 表名 | 记录数 |
|------|--------|
| students | 72 (含测试账号) |
| questions | 244 |
| exam_records | 按需记录 |

### 测试账号

| 角色 | 学号/工号 | 说明 |
|------|----------|------|
| 测试学生 | 123456 | 可直接登录测试 |
| 教师 | 654321 | 查看统计数据 |

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户访问入口                          │
│        https://hd-exam-system.pages.dev                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │      Cloudflare Pages 前端       │
         │  - index.html (首页入口)         │
         │  - exam.html (学生考试)          │
         │  - teacher.html (教师管理)       │
         └────────────────┬────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────┐
         │    Cloudflare Workers API        │
         │  https://hd-exam-api.xxx.workers.dev/api
         │  - /students (学生验证)          │
         │  - /chapters (章节列表)          │
         │  - /questions (题目查询)         │
         │  - /generate-exam (生成试卷)     │
         │  - /submit-exam (提交成绩)       │
         │  - /exam-records (考试记录)      │
         └────────────────┬────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────┐
         │       Cloudflare D1 数据库       │
         │   hd-exam-db (SQLite)           │
         │   - students 表                  │
         │   - questions 表                 │
         │   - exam_records 表              │
         └─────────────────────────────────┘
```

---

## 📝 文件结构

```
dist/
├── index.html          # 首页入口
├── exam.html           # 学生考试页面
├── teacher.html        # 教师管理页面
├── _headers            # 安全头配置
├── _redirects          # URL 重定向配置
└── DEPLOY_GUIDE.md     # 部署指南

cloudflare-worker/
├── src/worker.js       # Worker API 代码
└── wrangler.toml       # Worker 配置

config/
├── URLS_README.md      # 本文档
└── agent_llm_config.json # 模型配置
```

---

## ✅ 验证部署

### API 验证

```bash
# 测试章节列表
curl https://hd-exam-api.771794850.workers.dev/api/chapters

# 测试学生验证
curl https://hd-exam-api.771794850.workers.dev/api/students
```

### 前端验证

1. 访问 https://hd-exam-system.pages.dev
2. 点击"学生考试入口"
3. 输入测试学号：123456
4. 选择章节，开始答题

---

## 🆘 常见问题

### Q: 章节列表无法加载？
**A**: 检查 API 是否正常：
```bash
curl https://hd-exam-api.771794850.workers.dev/api/chapters
```
如果返回空数组或错误，可能需要重新导入数据。

### Q: 学生登录失败？
**A**: 确认学号正确。测试账号：123456

### Q: 如何更新前端？
**A**: 
```bash
cd /workspace/projects
# 修改 dist 目录中的文件后
wrangler pages deploy dist --project-name=hd-exam-system
```

---

*文档更新时间: 2024-03-30*
*最后部署: 2024-03-30 (commit c7b2d43)*
