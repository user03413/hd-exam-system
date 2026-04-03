# 📥 如何下载 miniprogram 文件夹

## 方法一：下载压缩包（已完成 ✅）

我已经帮您打包好了！

### 下载步骤：

**文件位置**：`/workspace/projects/miniprogram.tar.gz`

**下载方式**：

1. **在Coze文件管理器中下载**：
   - 在左侧文件浏览器中找到 `miniprogram.tar.gz`
   - 右键点击文件
   - 选择"下载"

2. **解压文件**：
   - Windows系统：使用 WinRAR 或 7-Zip 解压
   - Mac系统：双击自动解压
   - Linux系统：`tar -xzf miniprogram.tar.gz`

---

## 方法二：逐个文件下载（备选）

如果压缩包下载有问题，可以逐个下载文件：

### 核心文件列表：

```
miniprogram/
├── app.js                          # 小程序入口
├── app.json                        # 小程序配置
├── app.wxss                        # 全局样式
├── pages/
│   ├── index/                      # 首页
│   │   ├── index.js
│   │   ├── index.wxml
│   │   └── index.wxss
│   ├── student/                    # 学生端
│   │   ├── login/
│   │   │   ├── login.js
│   │   │   ├── login.wxml
│   │   │   └── login.wxss
│   │   ├── exam/
│   │   │   ├── exam.js
│   │   │   ├── exam.wxml
│   │   │   └── exam.wxss
│   │   └── result/
│   │       ├── result.js
│   │       ├── result.wxml
│   │       └── result.wxss
│   └── teacher/                    # 教师端
│       ├── login/
│       │   ├── login.js
│       │   ├── login.wxml
│       │   └── login.wxss
│       ├── stats/
│       │   ├── stats.js
│       │   ├── stats.wxml
│       │   └── stats.wxss
│       └── chapter/
│           ├── chapter.js
│           ├── chapter.wxml
│           └── chapter.wxss
└── utils/
    ├── request.js                  # API封装
    └── util.js                     # 工具函数
```

**下载方式**：
- 在文件浏览器中找到对应文件
- 右键 → 下载
- 在本地创建相同的文件夹结构
- 将下载的文件放入对应位置

---

## 方法三：从GitHub下载（推荐 ⭐⭐⭐）

**最简单的方式**！

### 操作步骤：

1. **访问GitHub仓库**：
   ```
   https://github.com/user03413/hd-exam-system
   ```

2. **下载项目**：
   - 点击绿色按钮 "Code"
   - 选择 "Download ZIP"

3. **解压文件**：
   - 解压下载的 ZIP 文件
   - 找到 `miniprogram` 文件夹

4. **导入开发者工具**：
   - 打开微信开发者工具
   - 导入项目
   - 选择 `miniprogram` 文件夹

---

## 📦 文件信息

**压缩包**：
- 文件名：`miniprogram.tar.gz`
- 大小：13KB
- 格式：tar.gz（Linux/Mac原生支持，Windows需解压软件）

**包含内容**：
- 所有小程序页面文件
- 工具类文件
- 配置文件
- 样式文件

---

## ✅ 推荐方案

**最快速**：从GitHub下载（方法三）
- 直接下载ZIP
- 一键解压
- 无需逐个文件操作

**最稳定**：下载压缩包（方法一）
- 已为您打包好
- 包含所有必需文件

---

## 🔧 解压后验证

解压后，请确认 `miniprogram` 文件夹包含以下文件：

✅ **必需文件**：
- [ ] app.js
- [ ] app.json
- [ ] app.wxss
- [ ] pages/ 文件夹
- [ ] utils/ 文件夹

如果以上文件都存在，说明下载成功！

---

## 💡 使用提示

下载完成后：

1. 在微信开发者工具中选择 `miniprogram` 文件夹
2. 填入您的AppID
3. 点击"导入"
4. 开始测试

---

*更新时间: 2026-03-26*
