"""生成热工自动控制试题"""
import os
import json
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage


# 教材章节信息
CHAPTERS = [
    {"num": "第一章", "title": "概论", "page": 1, "part": "第一篇"},
    {"num": "第二章", "title": "热工对象动态特性", "page": 10, "part": "第一篇"},
    {"num": "第三章", "title": "常规控制规律", "page": 33, "part": "第一篇"},
    {"num": "第四章", "title": "单回路控制系统", "page": 43, "part": "第一篇"},
    {"num": "第五章", "title": "串级控制系统", "page": 66, "part": "第一篇"},
    {"num": "第六章", "title": "前馈-反馈控制系统", "page": 77, "part": "第一篇"},
    {"num": "第七章", "title": "比值控制系统", "page": 83, "part": "第一篇"},
    {"num": "第八章", "title": "其他复杂控制系统", "page": 90, "part": "第一篇"},
    {"num": "第九章", "title": "多变量控制系统", "page": 100, "part": "第一篇"},
    {"num": "第十章", "title": "汽包锅炉蒸汽温度控制系统", "page": 114, "part": "第二篇"},
    {"num": "第十一章", "title": "汽包锅炉给水控制系统", "page": 132, "part": "第二篇"},
    {"num": "第十二章", "title": "锅炉燃烧过程控制系统", "page": 153, "part": "第二篇"},
]


def generate_questions_batch(
    client: LLMClient,
    question_type: str,
    chapter: dict,
    count: int = 10,
    difficulty_distribution: dict = None
) -> list:
    """
    批量生成试题
    
    Args:
        client: LLM客户端
        question_type: 题目类型 (single_choice, multiple_choice, short_answer)
        chapter: 章节信息
        count: 生成题目数量
        difficulty_distribution: 难度分布 {"基础": 3, "中等": 4, "困难": 3}
        
    Returns:
        题目列表
    """
    if difficulty_distribution is None:
        difficulty_distribution = {"基础": 3, "中等": 4, "困难": 3}
    
    # 构建提示词
    type_prompts = {
        "single_choice": """生成单选题，格式如下：
{
  "questions": [
    {
      "question": "题目内容",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
      "answer": "A",
      "analysis": "解析说明",
      "difficulty": "基础/中等/困难",
      "chapter": "章节号",
      "page": "页码"
    }
  ]
}""",
        
        "multiple_choice": """生成多选题（至少两个正确答案），格式如下：
{
  "questions": [
    {
      "question": "题目内容",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
      "answer": ["A", "C"],
      "analysis": "解析说明",
      "difficulty": "基础/中等/困难",
      "chapter": "章节号",
      "page": "页码"
    }
  ]
}""",
        
        "short_answer": """生成简答题，格式如下：
{
  "questions": [
    {
      "question": "题目内容",
      "answer": "标准答案要点（分条列出）",
      "analysis": "详细解析",
      "difficulty": "基础/中等/困难",
      "chapter": "章节号",
      "page": "页码"
    }
  ]
}"""
    }
    
    system_prompt = f"""你是一位专业的热工自动控制技术试题编写专家。
教材：《火电厂热工自动控制技术及应用》
作者：刘禾、白焰、李新利
出版社：中国电力出版社

当前章节：{chapter['part']} - {chapter['num']} {chapter['title']}（第{chapter['page']}页）

请基于该章节的核心知识点，生成 {count} 道高质量试题。
难度分布：基础{difficulty_distribution.get('基础', 0)}道、中等{difficulty_distribution.get('中等', 0)}道、困难{difficulty_distribution.get('困难', 0)}道

要求：
1. 题目准确、专业，符合热工自动控制领域的实际情况
2. 答案正确，解析详细
3. 难度层次分明
4. 章节标注准确，页码范围合理

{type_prompts[question_type]}"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请生成 {count} 道{'单选题' if question_type == 'single_choice' else '多选题' if question_type == 'multiple_choice' else '简答题'}，覆盖{chapter['title']}的核心知识点。")
    ]
    
    print(f"正在生成 {chapter['num']} {chapter['title']} 的{'单选题' if question_type == 'single_choice' else '多选题' if question_type == 'multiple_choice' else '简答题'}...")
    
    response = client.invoke(
        messages=messages,
        model="doubao-seed-1-8-251228",
        temperature=0.7,
        max_completion_tokens=8192
    )
    
    # 处理响应内容
    content = response.content
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = " ".join([item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"])
    else:
        text = str(content)
    
    # 提取JSON
    try:
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            # 尝试找到JSON对象
            import re
            match = re.search(r'\{.*"questions".*\}', text, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                json_str = text.strip()
        
        result = json.loads(json_str)
        questions = result.get("questions", [])
        
        # 为每个问题添加章节信息
        for q in questions:
            if "chapter" not in q:
                q["chapter"] = chapter['num']
            if "page" not in q:
                q["page"] = str(chapter['page'])
            q["chapter_title"] = chapter['title']
        
        return questions
        
    except Exception as e:
        print(f"解析JSON失败: {e}")
        print(f"原始文本: {text[:500]}")
        return []


def generate_all_questions():
    """生成所有试题"""
    print("初始化LLM客户端...")
    ctx = new_context(method="generate_questions")
    client = LLMClient(ctx=ctx)
    
    all_questions = {
        "single_choice": [],
        "multiple_choice": [],
        "short_answer": []
    }
    
    # 单选题：50道，覆盖所有章节
    print("\n===== 生成单选题 =====")
    single_choice_count_per_chapter = {
        "第一章": 4, "第二章": 5, "第三章": 5, "第四章": 5, "第五章": 5,
        "第六章": 4, "第七章": 4, "第八章": 4, "第九章": 4, "第十章": 4,
        "第十一章": 3, "第十二章": 3
    }
    
    for chapter in CHAPTERS[:12]:  # 前12章
        count = single_choice_count_per_chapter.get(chapter['num'], 4)
        questions = generate_questions_batch(
            client, "single_choice", chapter, count,
            {"基础": count // 3, "中等": count // 3, "困难": count - count // 3 * 2}
        )
        all_questions["single_choice"].extend(questions)
        print(f"已生成 {len(questions)} 道单选题，累计 {len(all_questions['single_choice'])} 道")
    
    # 多选题：30道，覆盖主要章节
    print("\n===== 生成多选题 =====")
    multiple_choice_count_per_chapter = {
        "第一章": 3, "第二章": 3, "第三章": 3, "第四章": 3, "第五章": 3,
        "第六章": 2, "第七章": 2, "第八章": 2, "第九章": 3, "第十章": 2,
        "第十一章": 2, "第十二章": 2
    }
    
    for chapter in CHAPTERS[:12]:
        count = multiple_choice_count_per_chapter.get(chapter['num'], 2)
        questions = generate_questions_batch(
            client, "multiple_choice", chapter, count,
            {"基础": 1, "中等": 1, "困难": 1}
        )
        all_questions["multiple_choice"].extend(questions)
        print(f"已生成 {len(questions)} 道多选题，累计 {len(all_questions['multiple_choice'])} 道")
    
    # 简答题：20道，覆盖主要章节
    print("\n===== 生成简答题 =====")
    short_answer_count_per_chapter = {
        "第二章": 2, "第三章": 2, "第四章": 2, "第五章": 2, "第六章": 2,
        "第九章": 2, "第十章": 2, "第十一章": 2, "第十二章": 2, "第一章": 2
    }
    
    for chapter in CHAPTERS[:12]:
        count = short_answer_count_per_chapter.get(chapter['num'], 0)
        if count == 0:
            continue
        questions = generate_questions_batch(
            client, "short_answer", chapter, count,
            {"基础": 1, "中等": 1, "困难": 0}
        )
        all_questions["short_answer"].extend(questions)
        print(f"已生成 {len(questions)} 道简答题，累计 {len(all_questions['short_answer'])} 道")
    
    return all_questions


if __name__ == "__main__":
    print("开始生成试题...")
    questions = generate_all_questions()
    
    # 保存结果
    output_path = "/tmp/generated_questions.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n试题生成完成！")
    print(f"单选题: {len(questions['single_choice'])} 道")
    print(f"多选题: {len(questions['multiple_choice'])} 道")
    print(f"简答题: {len(questions['short_answer'])} 道")
    print(f"总计: {sum(len(v) for v in questions.values())} 道")
    print(f"已保存到: {output_path}")
