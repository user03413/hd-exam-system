"""
提交答案示例
演示完整的答题提交流程
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api/exam"


def verify_student(student_id: str) -> str:
    """验证学号并返回 session_id"""
    response = requests.post(
        f"{BASE_URL}/verify",
        json={"student_id": student_id}
    )
    result = response.json()
    
    if result.get("success"):
        print(f"验证成功: {result['student']['name']}")
        return result["session_id"]
    else:
        raise Exception(f"验证失败: {result.get('message')}")


def start_exam(session_id: str) -> list:
    """开始考试并返回题目列表"""
    response = requests.post(
        f"{BASE_URL}/start",
        json={"session_id": session_id}
    )
    result = response.json()
    
    if result.get("success"):
        print(f"开始时间: {result.get('start_time')}")
        return result["questions"]
    else:
        raise Exception(f"开始考试失败: {result.get('message')}")


def submit_answers(session_id: str, answers: dict) -> dict:
    """
    提交答案
    
    Args:
        session_id: 会话ID
        answers: 答案字典
            - 单选题: {"1": "A"}
            - 多选题: {"5": ["A", "B", "C"]}
            - 简答题: {"8": "这是答案内容"}
    
    Returns:
        dict: 判分结果
    """
    response = requests.post(
        f"{BASE_URL}/submit",
        json={
            "session_id": session_id,
            "answers": answers
        }
    )
    return response.json()


def main():
    # 1. 验证学号
    print("=" * 50)
    print("火电机组考核系统 - 提交答案示例")
    print("=" * 50)
    
    student_id = "220252216150"  # 吴萌
    
    print(f"\n1. 验证学号: {student_id}")
    session_id = verify_student(student_id)
    
    # 2. 开始考试
    print("\n2. 开始考试...")
    questions = start_exam(session_id)
    
    # 3. 构建答案
    print("\n3. 构建答案...")
    
    # 模拟答题（实际应用中由用户输入）
    answers = {}
    for q in questions:
        seq = str(q["seq"])
        
        if q["type"] == "单选题":
            # 单选题：选择第一个选项
            answers[seq] = list(q["options"].keys())[0]
        
        elif q["type"] == "多选题":
            # 多选题：选择前两个选项
            options = list(q["options"].keys())
            answers[seq] = options[:2]
        
        elif q["type"] == "简答题":
            # 简答题：填写测试答案
            answers[seq] = "这是测试答案内容"
    
    print(f"已填写 {len(answers)} 道题")
    
    # 4. 模拟答题时间
    print("\n4. 模拟答题中（等待5秒）...")
    time.sleep(5)
    
    # 5. 提交答案
    print("\n5. 提交答案...")
    result = submit_answers(session_id, answers)
    
    if result.get("success"):
        print("\n" + "=" * 50)
        print("考核结果")
        print("=" * 50)
        
        print(f"\n得分: {result['score']} 分")
        print(f"开始时间: {result.get('start_time')}")
        print(f"结束时间: {result.get('end_time')}")
        print(f"考试用时: {result.get('duration')}")
        
        # 统计正确/错误/部分得分
        correct = sum(1 for r in result['results'] if r['is_correct'])
        partial = sum(1 for r in result['results'] if not r['is_correct'] and r['score'] > 0)
        wrong = len(result['results']) - correct - partial
        
        print(f"\n正确: {correct} 题")
        print(f"部分得分: {partial} 题")
        print(f"错误: {wrong} 题")
        
        # 打印每题详情
        print("\n答题详情:")
        for r in result['results']:
            status = "✓" if r['is_correct'] else ("△" if r['score'] > 0 else "✗")
            print(f"  第{r['seq']}题 [{r['type']}]: {r['score']}分 {status}")
    else:
        print(f"提交失败: {result.get('message')}")


if __name__ == "__main__":
    main()
