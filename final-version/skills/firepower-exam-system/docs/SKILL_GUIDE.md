# 技能调用指南

本文档说明如何在项目中调用各项技能服务。

---

## 1. LLM (大语言模型) 技能

### 用途
- 简答题评分
- 答案解析生成

### 调用方式

```python
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context

# 创建客户端
ctx = new_context(method="llm_call")
client = LLMClient(ctx=ctx)

# 调用模型
response = client.chat(
    messages=[
        {"role": "system", "content": "你是一个专业的热工自动控制领域评分专家。"},
        {"role": "user", "content": f"题目：{question}\n学生答案：{student_answer}\n参考答案：{correct_answer}\n请判断是否正确并给出评分。"}
    ],
    model="doubao-seed-1-6-251015",
    temperature=0.3
)

print(response.content)
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| messages | list | 消息列表 |
| model | string | 模型名称 |
| temperature | float | 温度参数 (0-1) |
| max_tokens | int | 最大输出token数 |

### 推荐模型

- `doubao-seed-1-6-251015` - 豆包模型（推荐）
- `deepseek-chat` - DeepSeek 模型

---

## 2. Web Search (联网搜索) 技能

### 用途
- 获取前沿拓展内容
- 搜索行业最新资讯

### 调用方式

```python
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context

# 创建客户端
ctx = new_context(method="web_search")
client = SearchClient(ctx=ctx)

# 执行搜索
response = client.web_search(
    query="火电厂热工自动控制 最新技术 行业案例",
    count=3,
    need_summary=True
)

# 处理结果
for item in response.web_items:
    print(f"标题: {item.title}")
    print(f"来源: {item.site_name}")
    print(f"摘要: {item.snippet}")
    print(f"链接: {item.url}")

# AI总结
if response.summary:
    print(f"总结: {response.summary}")
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| query | string | 搜索关键词 |
| count | int | 返回结果数量 |
| need_summary | bool | 是否需要AI总结 |

### 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| web_items | list | 搜索结果列表 |
| summary | string | AI总结内容 |

---

## 3. Document Generation (文档生成) 技能

### 用途
- 生成 PDF 学习报告
- 生成 DOCX 文档

### 调用方式

```python
from coze_coding_dev_sdk import DocumentGenerationClient

# 创建客户端
client = DocumentGenerationClient()

# 从 Markdown 生成 PDF
pdf_url = client.create_pdf_from_markdown(
    content="""
# 学习报告

## 基本信息
- 姓名：张三
- 学号：220252216068

## 成绩
- 得分：85分
""",
    title="学习报告_张三_20250311"
)

print(f"PDF下载链接: {pdf_url}")
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| content | string | Markdown 内容 |
| title | string | 文件标题 |

### 返回值

返回 PDF 文件的下载链接（有效期24小时）。

---

## 4. 综合使用示例

### 完整的判分流程

```python
from coze_coding_dev_sdk import LLMClient, SearchClient, DocumentGenerationClient
from coze_coding_utils.runtime_ctx.context import new_context

def process_exam_submission(session_id: str, answers: dict):
    """处理考试提交"""
    
    # 1. 获取会话信息
    session = exam_sessions[session_id]
    questions = session['questions']
    
    # 2. 判分（使用 LLM 评估简答题）
    ctx = new_context(method="grading")
    llm = LLMClient(ctx=ctx)
    
    results = []
    total_score = 0
    
    for q in questions:
        user_answer = answers.get(str(q['seq']), '')
        
        if q['type'] == '简答题':
            # 使用 LLM 评分
            prompt = f"""
            题目：{q['question']}
            学生答案：{user_answer}
            参考答案：{q['answer']}
            
            请判断学生答案是否正确（关键词匹配度>=60%为正确）。
            返回格式：{{"is_correct": true/false, "score": 0-10}}
            """
            response = llm.chat(messages=[{"role": "user", "content": prompt}])
            # 解析结果...
        else:
            # 选择题直接对比
            is_correct = (user_answer == q['answer'])
            score = 10 if is_correct else 0
        
        total_score += score
        results.append({...})
    
    # 3. 生成报告（使用 Document Generation）
    doc_client = DocumentGenerationClient()
    report_md = generate_report_markdown(session, results, total_score)
    pdf_url = doc_client.create_pdf_from_markdown(report_md, f"report_{session_id}")
    
    return {
        "score": total_score,
        "results": results,
        "report_url": pdf_url
    }
```

### 获取前沿拓展

```python
def get_extension(question: str, chapter_title: str) -> str:
    """获取题目的前沿拓展"""
    
    ctx = new_context(method="extension")
    client = SearchClient(ctx=ctx)
    
    # 构建搜索词
    query = f"火电厂热工自动控制 {chapter_title} 最新技术 行业案例"
    
    # 搜索
    response = client.web_search(
        query=query,
        count=3,
        need_summary=True
    )
    
    # 格式化输出
    content = "## 前沿拓展\n\n"
    
    if response.web_items:
        content += "### 相关资讯\n\n"
        for i, item in enumerate(response.web_items, 1):
            content += f"**{i}. {item.title}**\n\n"
            content += f"来源：{item.site_name}\n\n"
            if item.snippet:
                content += f"{item.snippet}\n\n"
            content += f"[查看详情]({item.url})\n\n"
    
    if response.summary:
        content += f"### AI总结\n\n{response.summary}\n\n"
    
    return content
```

---

## 5. 错误处理

```python
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context

def safe_llm_call(prompt: str, max_retries: int = 3) -> str:
    """安全的 LLM 调用，带重试"""
    
    for attempt in range(max_retries):
        try:
            ctx = new_context(method="llm_call")
            client = LLMClient(ctx=ctx)
            
            response = client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="doubao-seed-1-6-251015",
                timeout=30
            )
            
            return response.content
            
        except Exception as e:
            print(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return "服务暂时不可用，请稍后重试"
            time.sleep(2)
    
    return "服务暂时不可用"
```

---

## 6. 性能优化建议

1. **复用客户端实例**: 避免每次调用都创建新客户端
2. **异步调用**: 使用 async/await 提高并发
3. **缓存结果**: 相同问题的拓展内容可缓存
4. **超时设置**: 合理设置超时时间，避免长时间等待

```python
# 推荐做法：复用客户端
class ExamService:
    def __init__(self):
        self.ctx = new_context(method="exam_service")
        self.llm_client = LLMClient(ctx=self.ctx)
        self.search_client = SearchClient(ctx=self.ctx)
        self.doc_client = DocumentGenerationClient()
    
    def grade_short_answer(self, question, answer, reference):
        return self.llm_client.chat(...)
    
    def get_extension(self, chapter):
        return self.search_client.web_search(...)
```
