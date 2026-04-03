# API 接口文档

## 基础信息

- **Base URL**: `/api/exam`
- **Content-Type**: `application/json`
- **响应格式**: JSON

---

## 接口列表

### 1. 学号验证

验证学生身份并创建会话。

**请求**

```
POST /api/exam/verify
```

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学号（12位数字）|

**示例请求**

```json
{
  "student_id": "220252216068"
}
```

**成功响应**

```json
{
  "success": true,
  "message": "验证成功，欢迎 曾俊 同学！",
  "student": {
    "id": "220252216068",
    "name": "曾俊",
    "major": "控制工程"
  },
  "session_id": "a1b2c3d4e5f6g7h8"
}
```

**失败响应**

```json
{
  "success": false,
  "message": "学号不存在，请检查输入"
}
```

---

### 2. 开始考试

开始考试并抽取题目。

**请求**

```
POST /api/exam/start
```

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID（从验证接口获取）|

**示例请求**

```json
{
  "session_id": "a1b2c3d4e5f6g7h8"
}
```

**成功响应**

```json
{
  "success": true,
  "questions": [
    {
      "seq": 1,
      "type": "单选题",
      "question": "微分控制规律的特点是（ ）。",
      "options": {
        "A": "对输入的变化率进行响应",
        "B": "立即消除稳态误差",
        "C": "与输入的大小成比例",
        "D": "输出与输入变化无关系"
      },
      "chapter": "第三章",
      "chapter_title": "常规控制规律",
      "difficulty": "困难"
    }
  ],
  "total": 10,
  "start_time": "2025-03-11 10:00:00"
}
```

---

### 3. 提交答案

提交答题结果并获取判分。

**请求**

```
POST /api/exam/submit
```

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID |
| answers | object | 是 | 答案对象 |

**答案格式**

```json
{
  "answers": {
    "1": "A",              // 单选题：字符串
    "2": "B",
    "5": ["A", "B", "C"],  // 多选题：数组
    "6": ["A", "C"],
    "7": "这是简答题答案",  // 简答题：字符串
    "8": "另一个答案"
  }
}
```

**示例请求**

```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": ["A", "B"],
    "6": ["A", "C"],
    "7": "积分控制的作用是消除余差...",
    "8": "选择性控制系统用于...",
    "9": "解耦控制的目的是...",
    "10": "锅炉燃烧控制..."
  }
}
```

**成功响应**

```json
{
  "success": true,
  "score": 70,
  "results": [
    {
      "seq": 1,
      "type": "单选题",
      "question": "微分控制规律的特点是（ ）。",
      "options": {...},
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "score": 10,
      "analysis": "微分控制规律是根据输入的变化率...",
      "chapter": "第三章",
      "chapter_title": "常规控制规律",
      "page": "33",
      "difficulty": "困难"
    }
  ],
  "start_time": "2025-03-11 10:00:00",
  "end_time": "2025-03-11 10:15:30",
  "duration": "15分30秒",
  "duration_seconds": 930
}
```

---

### 4. 获取前沿拓展

获取题目的前沿拓展内容。

**请求**

```
POST /api/exam/extension
```

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 题目内容 |
| chapter_title | string | 是 | 章节名称 |

**示例请求**

```json
{
  "question": "微分控制规律的特点是什么？",
  "chapter_title": "常规控制规律"
}
```

**成功响应**

```json
{
  "success": true,
  "extension": "## 前沿拓展\n\n### 相关最新资讯\n\n1. **智能控制在热工过程中的应用**\n..."
}
```

---

### 5. 导出学习报告

导出 PDF 格式的学习报告。

**请求**

```
POST /api/exam/export
```

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID |
| extensions | object | 否 | 前沿拓展内容 |

**示例请求**

```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "extensions": {
    "1": "## 前沿拓展\n...",
    "2": "## 前沿拓展\n..."
  }
}
```

**成功响应**

```json
{
  "success": true,
  "download_url": "https://example.com/report.pdf",
  "message": "报告生成成功"
}
```

---

## 错误码

| 错误信息 | 说明 |
|----------|------|
| 会话无效，请重新登录 | session_id 不存在或已过期 |
| 学号不存在，请检查输入 | 学号不在名单中 |
| 未获取题目 | 未调用开始考试接口 |
| 验证失败：xxx | 系统错误，附带详细错误信息 |

---

## 完整调用流程

```python
import requests

BASE_URL = "https://your-domain.com/api/exam"

# 1. 验证学号
resp = requests.post(f"{BASE_URL}/verify", json={
    "student_id": "220252216068"
})
data = resp.json()
session_id = data["session_id"]

# 2. 开始考试
resp = requests.post(f"{BASE_URL}/start", json={
    "session_id": session_id
})
questions = resp.json()["questions"]

# 3. 提交答案
answers = {
    "1": "A",
    "2": "B",
    # ...
}
resp = requests.post(f"{BASE_URL}/submit", json={
    "session_id": session_id,
    "answers": answers
})
result = resp.json()
print(f"得分: {result['score']}")
print(f"用时: {result['duration']}")

# 4. 导出报告
resp = requests.post(f"{BASE_URL}/export", json={
    "session_id": session_id,
    "extensions": {}
})
print(f"报告下载: {resp.json()['download_url']}")
```
