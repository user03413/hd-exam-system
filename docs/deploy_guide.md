# 火电机组考核系统 - 部署指南

## 当前部署状态

✅ 已成功部署到对象存储

**访问链接**: 
```
https://coze-coding-project.tos.coze.site/coze_storage_7615535867213578280/exam-system/1773819718/index_996d32d3.html?sign=1776411719-da7db14bd1-0-5503903bdfa3a23e8d3648ece5a96fcdc00ee95a0f11e0fceb06ad7bc491bfe3
```

> ⚠️ 此链接有效期为30天

## 如何获取永久链接

### 方案1: Cloudflare Pages (推荐)

**步骤:**
1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 **Workers & Pages** → **Create application** → **Pages**
3. 选择 **Upload assets**
4. 上传 `dist` 目录中的所有文件
5. 项目命名为 `hd-exam-system`
6. 部署完成后获得永久链接: `https://hd-exam-system.pages.dev`

**或使用命令行:**
```bash
# 安装 wrangler
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署
wrangler pages deploy dist --project-name=hd-exam-system
```

### 方案2: GitHub Pages

**步骤:**
1. 创建 GitHub 仓库
2. 上传 `dist` 目录内容到仓库
3. 进入 Settings → Pages
4. 选择分支和目录
5. 保存后获得链接: `https://<用户名>.github.io/<仓库名>`

### 方案3: Vercel

**步骤:**
1. 访问 [Vercel](https://vercel.com/new)
2. 拖拽上传 `dist` 目录
3. 自动获得永久链接

### 方案4: Netlify Drop

**步骤:**
1. 访问 [Netlify Drop](https://app.netlify.com/drop)
2. 拖拽上传 `dist` 目录
3. 自动获得永久链接

## 部署文件位置

```
dist/
├── index.html          # 主页面（离线版考试系统）
├── exam_records.json   # 考试记录
├── image.png          # 图片资源
└── *.xlsx             # 题库和学生名单
```

## 功能说明

| 功能 | 说明 |
|------|------|
| 学生考试 | 访问首页即可开始考试 |
| 测试账号 | 学号 `123456` |
| 教师账号 | 工号 `654321` |

## 自动部署脚本

已创建以下部署脚本:

| 脚本 | 说明 |
|------|------|
| `scripts/deploy.py` | Cloudflare Pages 部署 |
| `scripts/deploy_static.py` | 多平台部署 |
| `scripts/deploy_to_storage.py` | 对象存储部署 |
| `scripts/deploy_to_cloudflare.py` | Cloudflare 完整部署 |

## 使用方法

```bash
# 部署到对象存储（当前方案）
python scripts/deploy_to_storage.py

# 部署到 Cloudflare Pages（需要API Token或登录）
CLOUDFLARE_API_TOKEN=xxx CLOUDFLARE_ACCOUNT_ID=xxx python scripts/deploy.py

# 部署到多个平台（自动选择可用平台）
python scripts/deploy_static.py
```

## 环境变量

| 变量 | 说明 | 用途 |
|------|------|------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token | Cloudflare Pages 部署 |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID | Cloudflare Pages 部署 |
| `VERCEL_TOKEN` | Vercel Token | Vercel 部署 |
| `NETLIFY_TOKEN` | Netlify Token | Netlify 部署 |
| `GITHUB_TOKEN` | GitHub Token | GitHub Pages 部署 |

---

**部署时间**: 2026-03-18 15:41:59
