# 火电机组考核系统 - 技能库

> 封装开发和部署过程中的固定流程，提高开发效率

## 📦 技能列表

### 1. 数据同步技能 (data-sync)

**用途**: 从 Excel 文件同步学生名单和题库数据到 Cloudflare D1 数据库

```bash
# 同步学生名单
python skills/data-sync/student_sync.py

# 同步题库
python skills/data-sync/question_sync.py

# 指定 Excel 文件
python skills/data-sync/student_sync.py assets/学生名单.xlsx
```

**核心功能**:
- ✅ 从 Excel 读取学生/题库数据
- ✅ 自动生成 SQL 语句
- ✅ 同步到 D1 数据库
- ✅ 支持自定义数据源

---

### 2. Git 同步技能 (git-sync)

**用途**: 封装 Git 提交和推送操作

```bash
# 查看 Git 状态
python skills/git-sync/git_skill.py status

# Git 提交
python skills/git-sync/git_skill.py commit "feat: 新功能"

# Git 推送
python skills/git-sync/git_skill.py push

# 完整同步
python skills/git-sync/git_skill.py sync "sync: 更新"

# 快速同步（预设消息）
python skills/git-sync/git_skill.py quick_sync feat
```

**核心功能**:
- ✅ 查看仓库状态
- ✅ 自动添加所有变更
- ✅ 提交并推送到 GitHub
- ✅ 支持 Conventional Commits 规范

---

### 3. Cloudflare 部署技能 (cloudflare-deploy)

**用途**: 封装 Cloudflare Workers 和 D1 数据库的部署操作

```bash
# 获取 Worker 信息
python skills/cloudflare-deploy/cloudflare_skill.py info

# 部署 Worker
python skills/cloudflare-deploy/cloudflare_skill.py deploy

# 查询 D1 数据库
python skills/cloudflare-deploy/cloudflare_skill.py query "SELECT * FROM students LIMIT 10"

# 导入数据到 D1
python skills/cloudflare-deploy/cloudflare_skill.py import students.sql

# 获取数据库状态
python skills/cloudflare-deploy/cloudflare_skill.py status

# 完整部署
python skills/cloudflare-deploy/cloudflare_skill.py deploy_full
```

**核心功能**:
- ✅ 部署 Workers API
- ✅ 查询/操作 D1 数据库
- ✅ 导入 SQL 文件
- ✅ 获取部署状态

---

### 4. 系统检查技能 (system-check)

**用途**: 检查火电机组考核系统的运行状态

```bash
# 检查本地文件
python skills/system-check/system_check.py files

# 检查数据库
python skills/system-check/system_check.py database

# 检查 Git 状态
python skills/system-check/system_check.py git

# 检查凭证配置
python skills/system-check/system_check.py credentials

# 完整检查
python skills/system-check/system_check.py full

# 生成报告
python skills/system-check/system_check.py report
```

**核心功能**:
- ✅ 检查必需文件是否存在
- ✅ 验证数据库连接和数据量
- ✅ 检查 Git 状态和凭证配置
- ✅ 生成 Markdown 格式报告

---

### 5. 一键部署技能 (one-click)

**用途**: 整合所有技能，提供一键部署能力

```bash
# 显示技能信息
python skills/one-click/one_click_deploy.py info

# 一键同步部署
python skills/one-click/one_click_deploy.py sync_and_deploy

# 完整同步部署（包含数据）
python skills/one-click/one_click_deploy.py full_sync

# 快速部署
python skills/one-click/one_click_deploy.py quick_deploy

# 初始化部署
python skills/one-click/one_click_deploy.py init_deploy
```

**核心功能**:
- ✅ 整合所有技能流程
- ✅ 一键完成同步和部署
- ✅ 支持增量/完整部署

---

## 🚀 快速使用

### 场景1: 日常开发同步

当你修改了代码，需要同步到 GitHub 和 Cloudflare：

```bash
python skills/one-click/one_click_deploy.py sync_and_deploy "feat: 新增功能"
```

### 场景2: 更新学生名单

当学生名单有变动时：

```bash
# 1. 更新 Excel 文件
# 2. 执行同步
python skills/data-sync/student_sync.py
```

### 场景3: 更新题库

当题库有变化时：

```bash
# 1. 更新 Excel 文件
# 2. 执行同步
python skills/data-sync/question_sync.py
```

### 场景4: 系统问题排查

当系统出现问题时：

```bash
# 生成检查报告
python skills/system-check/system_check.py report
```

---

## 📁 目录结构

```
skills/
├── data-sync/              # 数据同步技能
│   ├── skill.json          # 技能配置
│   ├── student_sync.py     # 学生数据同步
│   └── question_sync.py    # 题库数据同步
│
├── git-sync/               # Git 同步技能
│   ├── skill.json          # 技能配置
│   └── git_skill.py        # Git 操作封装
│
├── cloudflare-deploy/      # Cloudflare 部署技能
│   ├── skill.json          # 技能配置
│   └── cloudflare_skill.py # Cloudflare 操作封装
│
├── system-check/           # 系统检查技能
│   ├── skill.json          # 技能配置
│   └── system_check.py     # 系统检查封装
│
└── one-click/              # 一键部署技能
    ├── skill.json          # 技能配置
    └── one_click_deploy.py # 一键部署封装
```

---

## ⚙️ 配置要求

### 凭证配置

在 `.config/credentials.json` 中配置：

```json
{
  "github": {
    "username": "your-username",
    "token": "ghp_xxxx",
    "repo": "https://github.com/username/repo.git"
  },
  "cloudflare": {
    "account_id": "your-account-id",
    "api_token": "your-api-token"
  }
}
```

### 环境变量

也可通过环境变量配置：

```bash
export GITHUB_USERNAME="user03413"
export GITHUB_TOKEN="ghp_xxxx"
export CLOUDFLARE_ACCOUNT_ID="57d6cde2xxx"
export CLOUDFLARE_API_TOKEN="cfut_xxxx"
```

---

## 📝 使用规范

### 命令约定

| 命令 | 说明 | 执行内容 |
|------|------|---------|
| **同步部署** | Git + Cloudflare | GitHub推送 + Worker部署 |
| **同步** | 仅 GitHub | Git提交并推送 |
| **部署** | 仅 Cloudflare | Worker部署 |

### 提交消息规范

遵循 Conventional Commits：

- `feat:` 新功能
- `fix:` 修复问题
- `docs:` 文档更新
- `chore:` 其他更新
- `sync:` 同步操作

---

## 🔗 相关链接

- **统一入口**: https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/
- **Cloudflare**: https://hd-exam-api.771794850.workers.dev/
- **GitHub**: https://github.com/user03413/hd-exam-system

---

*技能库版本: 1.0.0 | 最后更新: 2025-03-20*
