# 火电机组考核系统 - 微信小程序

## 📁 项目结构

```
miniprogram/
├── app.js                 # 小程序入口文件
├── app.json               # 小程序全局配置
├── app.wxss               # 小程序全局样式
├── project.config.json    # 项目配置文件
├── sitemap.json           # 站点地图配置
│
├── pages/                 # 页面目录
│   ├── index/             # 首页
│   │   ├── index.js
│   │   ├── index.wxml
│   │   └── index.wxss
│   │
│   ├── student/           # 学生端
│   │   ├── login/         # 登录页
│   │   ├── exam/          # 答题页
│   │   └── result/        # 成绩页
│   │
│   └── teacher/           # 教师端
│       ├── login/         # 登录页
│       ├── stats/         # 统计页
│       └── chapter/       # 章节出题
│
└── utils/                 # 工具目录
    ├── request.js         # API请求封装
    └── util.js            # 工具函数
```

## 🚀 快速开始

### 1. 导入项目

1. 打开微信开发者工具
2. 选择「导入项目」
3. 选择 `miniprogram` 文件夹
4. AppID 可使用测试号或填写 `touristappid`

### 2. 配置开发环境

**重要：开发环境必须关闭域名校验**

```
详情 → 本地设置 → 勾选「不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书」
```

### 3. 运行项目

点击「编译」按钮即可在模拟器中预览

## 📱 功能模块

### 学生端
- ✅ 学号登录验证
- ✅ 在线答题（单选/多选/简答）
- ✅ 实时计时
- ✅ 成绩查看
- ✅ 答案解析

### 教师端
- ✅ 工号登录
- ✅ 统计数据查看
- ✅ 章节出题
- ✅ 生成考试链接

## 🔑 测试账号

| 角色 | 账号 |
|------|------|
| 学生 | 123456 |
| 教师 | 654321 |

## ⚙️ 配置说明

### API 地址配置

在 `app.js` 中修改 `API_BASE_URL`：

```javascript
const API_BASE_URL = 'https://your-api-domain.com'
```

### 页面配置

在 `app.json` 的 `pages` 数组中添加/删除页面路径

## 📝 开发规范

### getApp() 调用规范

```javascript
// ❌ 错误：模块顶层调用
const app = getApp()

// ✅ 正确：函数内部调用
function myFunction() {
  try {
    const app = getApp()
    if (app && app.globalData) {
      // 使用 app.globalData
    }
  } catch (err) {
    console.error('获取 App 失败:', err)
  }
}
```

### 网络请求规范

```javascript
// 使用 utils/request.js 封装的方法
const api = require('../../../utils/request')

// 学生登录
const res = await api.verifyStudent(studentId, chapter)

// 教师登录
const res = await api.teacherLogin(teacherId)
```

## 🔧 常见问题

### Q1: 登录失败，提示 "Cannot read property 'globalData' of undefined"

**解决方案：**
1. 清除缓存：工具 → 清除缓存 → 清除全部缓存
2. 重新编译项目

### Q2: 网络请求失败

**解决方案：**
1. 确认已关闭域名校验
2. 检查 API 地址是否正确
3. 检查网络连接

### Q3: 页面样式异常

**解决方案：**
1. 检查 app.wxss 是否正确引入
2. 检查页面 wxss 文件是否存在

## 📄 许可证

MIT License

---

*更新时间: 2026-03-26*
