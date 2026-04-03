# 火电厂热工自动控制考核系统

## 📖 项目简介

基于《火电厂热工自动控制技术及应用》教材开发的在线考试平台，为控制工程专业学生提供便捷、公平、智能化的在线考核服务。

## 🎯 核心功能

| 功能模块 | 说明 |
|----------|------|
| 学号验证 | 基于 Excel 名单验证学生身份 |
| 随机抽题 | 从题库随机抽取 10 道题目 |
| 在线答题 | 支持单选、多选、简答三种题型 |
| 自动判分 | 提交后立即计算得分 |
| 时间记录 | 记录开始/结束时间及用时 |
| 前沿拓展 | 联网搜索相关技术最新资讯 |
| 学习报告 | 导出 PDF 学习报告 |

## 📁 文件结构

```
firepower-exam-system/
├── README.md                 # 项目说明
├── skill.json               # 技能配置（一键导入）
├── config.json              # 系统配置
├── requirements.txt         # Python 依赖
├── docs/                    # 文档目录
│   ├── ARCHITECTURE.md      # 系统架构
│   ├── API_REFERENCE.md     # API 接口文档
│   ├── SKILL_GUIDE.md       # 技能调用指南
│   └── DEPLOYMENT.md        # 部署说明
├── examples/                # 示例代码
│   ├── verify_student.py    # 学号验证示例
│   ├── generate_questions.py # 题目生成示例
│   ├── submit_exam.py       # 提交答案示例
│   └── export_report.py     # 导出报告示例
├── data/                    # 示例数据
│   ├── students.xlsx        # 学生名单模板
│   └── questions.xlsx       # 题库模板
└── templates/               # 模板文件
    ├── exam_page.html       # 考试页面模板
    └── report.md            # 报告模板
```

## 🚀 快速开始

### 1. 导入技能

在 Coze 或 Trae 中导入 `skill.json` 文件即可使用。

### 2. 配置数据文件

将学生名单和题库放到 `assets/` 目录：
- `assets/火电机组考核学生名单.xlsx`
- `assets/《火电厂热工自动控制技术及应用》_100题.xlsx`

### 3. 启动服务

```bash
python src/main.py -p 5000
```

### 4. 访问系统

打开浏览器访问：`http://localhost:5000/exam/real`

## 🔧 依赖技能

本系统依赖以下技能：

| 技能 | 用途 | 调用场景 |
|------|------|----------|
| LLM (大语言模型) | 简答题评分 | 自动判分模块 |
| Web Search (联网搜索) | 获取前沿拓展 | 前沿拓展模块 |
| Document Generation | 生成 PDF 报告 | 学习报告导出 |

## 📊 数据格式

### 学生名单格式

| 列名 | 类型 | 说明 |
|------|------|------|
| 学号 | string | 12位学号 |
| 姓名 | string | 学生姓名 |
| 专业 | string | 专业名称 |

### 题库格式

| 列名 | 类型 | 说明 |
|------|------|------|
| 题号 | int | 题目编号 |
| 章节 | string | 所属章节 |
| 章节名称 | string | 章节标题 |
| 页码 | int | 教材页码 |
| 题目内容 | string | 题目文本 |
| 选项A/B/C/D | string | 选项内容 |
| 答案 | string | 正确答案 |
| 解析 | string | 答案解析 |
| 难度 | string | 基础/中等/困难 |

## 📝 版本信息

- **版本**: v1.1
- **更新日期**: 2025-03-11
- **作者**: Coze AI 编程平台
