# 火电机组考核系统 - Cloudflare Pages 部署指南

## 🚀 快速部署（推荐）

### 方法一：Cloudflare Dashboard 手动部署

1. **登录 Cloudflare Dashboard**
   - 访问：https://dash.cloudflare.com
   - 进入 Pages 页面

2. **找到项目 `hd-exam-system`**
   - 如果不存在，点击 "Create a project" → "Direct Upload"

3. **上传 dist 目录**
   - 选择项目 → Deployments → Upload assets
   - 上传整个 `dist` 目录

### 方法二：使用 Wrangler CLI（需要 API Token）

```bash
# 设置环境变量
export CLOUDFLARE_API_TOKEN="你的API Token"
export CLOUDFLARE_ACCOUNT_ID="57d6cde2e053b14fd28bd963ddb0975b"

# 部署
cd /workspace/projects
wrangler pages deploy dist --project-name=hd-exam-system
```

### 方法三：GitHub 自动部署

1. **Fork 仓库到你的 GitHub**
   - 原仓库：https://github.com/user03413/hd-exam-system

2. **在 Cloudflare Pages 连接 GitHub**
   - Pages → Create project → Connect to Git
   - 选择仓库 `hd-exam-system`
   - 构建设置：
     - 构建命令：`echo "Static site, no build needed"`
     - 输出目录：`dist`

3. **每次推送自动部署**

---

## 📁 dist 目录结构

```
dist/
├── index.html          # 首页入口
├── exam.html           # 学生考试页面 ✨ 新增
├── teacher.html        # 教师管理页面 ✨ 新增
├── _headers            # 安全头配置
├── _redirects          # URL 重定向配置
├── exam_records.json   # 考试记录数据
├── image.png           # 图片资源
└── *.xlsx              # Excel 数据文件
```

---

## 🔗 访问地址

部署成功后访问：

| 服务 | URL |
|------|-----|
| **前端首页** | https://hd-exam-system.pages.dev |
| **学生考试** | https://hd-exam-system.pages.dev/exam |
| **教师管理** | https://hd-exam-system.pages.dev/teacher |
| **后端 API** | https://hd-exam-api.771794850.workers.dev/api |

---

## ✅ 验证部署成功

1. **访问首页**：https://hd-exam-system.pages.dev
   - 应该看到系统入口页面

2. **学生考试入口**：点击 "学生考试入口"
   - 输入学号验证（测试账号：123456）
   - 选择章节后开始答题

3. **教师管理入口**：点击 "教师管理入口"
   - 查看考试记录、统计数据

---

## ⚠️ 常见问题

### Q: 章节列表无法加载？
**A**: 确认 Worker API 正常运行：
```bash
curl https://hd-exam-api.771794850.workers.dev/api/chapters
```

### Q: 页面显示空白？
**A**: 检查浏览器控制台（F12）是否有跨域错误。Worker 已配置 CORS，应该正常工作。

### Q: 如何更新内容？
**A**: 重新上传 `dist` 目录，或推送代码到 GitHub 触发自动部署。

---

## 📝 更新日志

- **2024-03-30**: 新增 exam.html 和 teacher.html 前端页面
- **2024-03-30**: 配置 API 地址直接指向 Worker
- **2024-03-30**: 添加 _redirects 配置
