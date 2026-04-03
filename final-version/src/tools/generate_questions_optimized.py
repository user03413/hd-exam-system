"""优化的试题生成脚本 - 分批生成并保存"""
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


def get_text_content(response):
    """安全提取文本内容"""
    content = response.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return " ".join([item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"])
    else:
        return str(content)


def generate_questions_batch(
    client: LLMClient,
    question_type: str,
    chapters: list,
    total_count: int,
    output_file: str
):
    """
    批量生成试题并保存
    
    Args:
        client: LLM客户端
        question_type: 题目类型
        chapters: 章节列表
        total_count: 总题目数量
        output_file: 输出文件路径
    """
    # 加载已有数据
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
    else:
        all_questions = {"single_choice": [], "multiple_choice": [], "short_answer": []}
    
    existing_count = len(all_questions[question_type])
    print(f"已有 {existing_count} 道{'单选题' if question_type == 'single_choice' else '多选题' if question_type == 'multiple_choice' else '简答题'}")
    
    if existing_count >= total_count:
        print(f"已达到目标数量 {total_count}")
        return all_questions
    
    need_count = total_count - existing_count
    print(f"还需生成 {need_count} 道")
    
    # 构建提示词
    type_desc = {'single_choice': '单选题', 'multiple_choice': '多选题', 'short_answer': '简答题'}[question_type]
    
    type_format = {
        'single_choice': '''{
  "questions": [
    {
      "question": "题干",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "analysis": "解析",
      "difficulty": "基础/中等/困难"
    }
  ]
}''',
        'multiple_choice': '''{
  "questions": [
    {
      "question": "题干",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": ["A", "C"],
      "analysis": "解析",
      "difficulty": "基础/中等/困难"
    }
  ]
}''',
        'short_answer': '''{
  "questions": [
    {
      "question": "题干",
      "answer": "答案要点",
      "analysis": "详细解析",
      "difficulty": "基础/中等/困难"
    }
  ]
}'''
    }
    
    # 分批生成
    batch_size = 5  # 每次生成5道题
    generated = existing_count
    
    while generated < total_count:
        current_batch = min(batch_size, total_count - generated)
        
        # 随机选择章节
        import random
        chapter = random.choice(chapters)
        
        prompt = f"""作为热工自动控制专家，为《火电厂热工自动控制技术及应用》教材的{chapter['num']} {chapter['title']}章节生成 {current_batch} 道{type_desc}。

要求：
1. 专业准确，符合实际工程应用
2. 难度分布：基础、中等、困难各约1/3
3. 每题标注章节号和页码范围

输出JSON格式：
{type_format[question_type]}"""
        
        messages = [
            SystemMessage(content="你是热工自动控制技术试题编写专家，熟悉火电厂控制系统。"),
            HumanMessage(content=prompt)
        ]
        
        print(f"正在生成 {chapter['num']} 的{type_desc}（第{generated+1}-{min(generated+current_batch, total_count)}道）...")
        
        try:
            response = client.invoke(
                messages=messages,
                model="doubao-seed-1-6-flash-250615",  # 使用快速模型
                temperature=0.8,
                max_completion_tokens=4096
            )
            
            text = get_text_content(response)
            
            # 提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                questions = result.get("questions", [])
                
                # 添加章节信息
                for q in questions:
                    q["chapter"] = chapter['num']
                    q["chapter_title"] = chapter['title']
                    if "page" not in q:
                        q["page"] = str(chapter['page'])
                
                all_questions[question_type].extend(questions)
                generated += len(questions)
                
                # 保存进度
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_questions, f, ensure_ascii=False, indent=2)
                
                print(f"已生成 {len(questions)} 道，累计 {generated}/{total_count}")
            else:
                print("未找到JSON，跳过")
                
        except Exception as e:
            print(f"生成失败: {e}")
            continue
    
    return all_questions


if __name__ == "__main__":
    print("初始化LLM客户端...")
    ctx = new_context(method="generate_questions")
    client = LLMClient(ctx=ctx)
    
    output_file = "/tmp/generated_questions.json"
    
    # 生成单选题
    print("\n===== 生成单选题 =====")
    generate_questions_batch(client, "single_choice", CHAPTERS, 50, output_file)
    
    # 生成多选题
    print("\n===== 生成多选题 =====")
    generate_questions_batch(client, "multiple_choice", CHAPTERS, 30, output_file)
    
    # 生成简答题
    print("\n===== 生成简答题 =====")
    generate_questions_batch(client, "short_answer", CHAPTERS, 20, output_file)
    
    # 最终统计
    with open(output_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)
    
    print(f"\n===== 生成完成 =====")
    print(f"单选题: {len(final_data['single_choice'])} 道")
    print(f"多选题: {len(final_data['multiple_choice'])} 道")
    print(f"简答题: {len(final_data['short_answer'])} 道")
    print(f"总计: {sum(len(v) for v in final_data.values())} 道")
    print(f"保存到: {output_file}")
