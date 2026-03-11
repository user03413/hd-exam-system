"""
题目生成示例
演示如何调用开始考试接口获取随机题目
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/exam"

def start_exam(session_id: str) -> dict:
    """
    开始考试，获取随机题目
    
    Args:
        session_id: 从验证接口获取的会话ID
    
    Returns:
        dict: 包含题目列表和开始时间
    """
    url = f"{BASE_URL}/start"
    payload = {"session_id": session_id}
    
    response = requests.post(url, json=payload)
    return response.json()


def print_questions(questions: list):
    """格式化打印题目"""
    for q in questions:
        print(f"\n【第{q['seq']}题】{q['type']} ({q['difficulty']})")
        print(f"章节: {q['chapter']} {q['chapter_title']}")
        print(f"题目: {q['question']}")
        
        if q['options']:
            print("选项:")
            for opt, content in q['options'].items():
                print(f"  {opt}. {content}")


def main():
    # 首先验证学号获取 session_id
    student_id = "220252216068"
    
    print("1. 验证学号...")
    verify_result = requests.post(
        f"{BASE_URL}/verify",
        json={"student_id": student_id}
    ).json()
    
    if not verify_result.get("success"):
        print(f"验证失败: {verify_result.get('message')}")
        return
    
    session_id = verify_result["session_id"]
    print(f"验证成功，欢迎 {verify_result['student']['name']}！")
    
    # 开始考试
    print("\n2. 开始考试...")
    exam_result = start_exam(session_id)
    
    if not exam_result.get("success"):
        print(f"开始考试失败: {exam_result.get('message')}")
        return
    
    print(f"开始时间: {exam_result.get('start_time')}")
    print(f"题目数量: {exam_result.get('total')}")
    
    # 打印题目
    print("\n" + "=" * 50)
    print("考试题目")
    print("=" * 50)
    print_questions(exam_result['questions'])


if __name__ == "__main__":
    main()
