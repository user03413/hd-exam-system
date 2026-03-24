# 火电机组考核系统 - 网址配置说明

> **最后更新**: 2026-03-23  
> **配置文件**: `config/urls.json`

---

## 📍 网址分类

### 一、Coze 平台生成的网址

> **来源**: Coze 平台自动生成  
> **特点**: 托管在 Coze 服务器，部署简单，功能完整

| 名称 | 网址 | 用途 |
|------|------|------|
| **统一入口** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/ | 首页，选择角色入口 |
| **学生考试** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/exam | 学生在线答题 |
| **教师后台** | https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/teacher | 教师管理功能 |

**推荐使用** ⭐：功能完整，体验优化，无需维护

---

### 二、Cloudflare 平台生成的网址

> **来源**: Cloudflare Workers 自动部署  
> **特点**: 边缘计算，全球加速，完全自主控制

| 名称 | 网址 | 用途 |
|------|------|------|
| **Workers API** | https://hd-exam-api.771794850.workers.dev | 后端 API 接口 |
| **Pages 前端** | https://hd-exam-system.pages.dev | 静态前端（备用） |

**功能说明**:
- ✅ 学生登录验证
- ✅ 题目获取与答题
- ✅ 成绩计算与保存
- ✅ 考试记录查询
- ✅ 统计分析

**数据库**:
- 类型: Cloudflare D1 (SQLite)
- ID: `0cc8b804-1e56-4563-9b8d-f45a76370192`
- 表: students, questions, exam_records

---

### 三、GitHub 仓库

> **来源**: 用户创建  
> **特点**: 代码托管，版本控制，协作开发

| 名称 | 网址 |
|------|------|
| **代码仓库** | https://github.com/user03413/hd-exam-system |

---

## 🎯 推荐使用方案

### 主用方案：Coze 平台

```
用户访问 Coze 统一入口
    ↓
Coze 前端界面
    ↓
调用 Cloudflare Workers API
    ↓
操作 D1 数据库
    ↓
返回数据展示
```

**优势**:
- ✅ 前端体验优化
- ✅ 自动部署更新
- ✅ 无需维护服务器
- ✅ 功能完整

---

### 备用方案：Cloudflare 独立运行

```
用户访问 Workers API
    ↓
直接调用后端接口
    ↓
操作 D1 数据库
```

**优势**:
- ✅ 完全自主控制
- ✅ 数据独立存储
- ✅ 可定制开发
- ✅ 全球CDN加速

---

## 📊 数据流向

```
┌─────────────────────────────────────────────────────────┐
│                    用户访问入口                          │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         │                                   │
    ┌────▼─────┐                      ┌─────▼────┐
    │  Coze    │                      │Cloudflare │
    │  前端    │                      │  前端     │
    └────┬─────┘                      └─────┬────┘
         │                                   │
         └──────────────┬───────────────────┘
                        ↓
              ┌─────────────────┐
              │ Cloudflare      │
              │ Workers API     │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ Cloudflare D1   │
              │ 数据库          │
              └─────────────────┘
```

---

## 🔧 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| **统一配置** | `config/urls.json` | 所有网址的统一配置 |
| **部署信息** | `deploy_info.json` | 详细的部署信息 |
| **凭证配置** | `.config/credentials.json` | API Token 等凭证 |

---

## ⚙️ 如何修改配置

### 修改网址

编辑 `config/urls.json` 文件：

```json
{
  "urls": {
    "coze_platform": {
      "endpoints": {
        "student_exam": {
          "url": "新的Coze网址"
        }
      }
    }
  }
}
```

### 在代码中读取

```python
import json

with open('config/urls.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    
# 获取 Coze 学生考试入口
exam_url = config['urls']['coze_platform']['endpoints']['student_exam']['url']

# 获取 Cloudflare Workers API
api_url = config['urls']['cloudflare_platform']['endpoints']['workers_api']['url']
```

---

## 📝 注意事项

1. **主推 Coze 入口**：推荐使用 Coze 平台的网址，体验更好
2. **API 互通**：Coze 前端调用 Cloudflare Workers API，两者配合使用
3. **数据同步**：两个平台共用同一个 Cloudflare D1 数据库
4. **备份机制**：如果 Coze 不可用，可直接使用 Cloudflare Workers API

---

## 🆘 常见问题

### Q: 应该用哪个网址？
**A**: 推荐使用 Coze 的统一入口：https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/

### Q: Cloudflare Workers API 有什么用？
**A**: 提供后端服务，处理考试逻辑、数据库操作。前端调用此 API。

### Q: 两个平台的数据互通吗？
**A**: 是的，都使用同一个 Cloudflare D1 数据库，数据完全同步。

### Q: 如何切换平台？
**A**: 直接访问对应平台的网址即可，数据是共享的。

---

*文档版本: 1.0 | 维护者: Coze AI Agent*
