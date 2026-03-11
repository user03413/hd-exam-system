# 系统架构文档

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Frontend)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  登录页面   │  │  答题页面   │  │  结果页面   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API层 (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │/verify   │ │/start    │ │/submit   │ │/export   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 学号验证模块  │ │ 题目抽取模块  │ │ 自动判分模块  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                         │
│  │ 前沿拓展模块  │ │ 报告生成模块  │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务集成层                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   LLM服务    │ │  Web Search  │ │   Doc Gen    │        │
│  │  (豆包模型)   │ │  (联网搜索)   │ │  (文档生成)   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│  ┌──────────────┐ ┌──────────────┐                         │
│  │  学生名单    │ │    题库      │                         │
│  │  (Excel)     │ │   (Excel)    │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块说明

### 1. 路由模块 (exam_routes.py)

负责处理所有 HTTP 请求，包括：
- 页面渲染
- API 接口处理
- 错误处理

### 2. 学生验证模块

```python
def load_students() -> Dict[str, Dict]:
    """从 Excel 加载学生名单"""
    df = pd.read_excel(STUDENT_FILE)
    students = {}
    for _, row in df.iterrows():
        student_id = str(int(row['学号']))
        students[student_id] = {
            'id': student_id,
            'name': row['姓名'],
            'major': row['专业']
        }
    return students
```

### 3. 题目抽取模块

```python
def random_select_questions(all_questions: Dict, count: int = 10) -> List:
    """随机抽取题目，保证题型分布"""
    single = random.sample(all_questions['单选题'], 4)
    multiple = random.sample(all_questions['多选题'], 3)
    short = random.sample(all_questions['简答题'], 3)
    return single + multiple + short
```

### 4. 自动判分模块

```python
def calculate_score(questions: List, answers: Dict) -> tuple:
    """计算得分并返回判分详情"""
    total_score = 0
    results = []
    for q in questions:
        # 单选题：完全匹配
        # 多选题：完全匹配
        # 简答题：关键词匹配
        score = evaluate_answer(q, answers.get(str(q['seq'])))
        total_score += score
        results.append(build_result(q, score))
    return total_score, results
```

### 5. 前沿拓展模块

```python
def get_extension_content(question: str, chapter_title: str) -> str:
    """调用 Web Search 获取前沿拓展"""
    search_client = SearchClient(ctx=ctx)
    response = search_client.web_search(
        query=f"火电厂热工自动控制 {chapter_title} 最新技术",
        count=3,
        need_summary=True
    )
    return format_extension(response)
```

### 6. 报告生成模块

```python
def generate_report(student_info, questions, results, score, extensions,
                    start_time, end_time, duration) -> str:
    """生成 Markdown 格式的学习报告"""
    # 构建报告内容
    report = build_report_markdown(...)
    return report
```

## 数据流

```
用户输入学号 → 验证 → 开始考试 → 抽题 → 答题 → 提交 → 判分 → 显示结果 → 导出报告
     │          │        │         │       │      │       │        │
     │          │        │         │       │      │       │        └→ Document Gen
     │          │        │         │       │      │       └→ 计算用时
     │          │        │         │       │      └→ 自动判分
     │          │        │         │       └→ 保存答案
     │          │        │         └→ 返回题目
     │          │        └→ 随机抽题
     │          └→ 生成 Session
     └→ Excel 验证
```

## 会话管理

使用内存字典存储会话状态：

```python
exam_sessions: Dict[str, Dict] = {}

# 会话结构
{
    "session_id": {
        "student": {...},
        "questions": [...],
        "answers": {...},
        "results": [...],
        "start_time": "2025-03-11T10:00:00",
        "end_time": "2025-03-11T10:15:00",
        "total_score": 85
    }
}
```

## 性能优化

1. **学生名单缓存**: 启动时加载一次，避免重复读取
2. **题库预加载**: 题库数据缓存在内存
3. **异步处理**: API 使用 async/await 提高并发
4. **前端优化**: 静态资源 CDN 加载
