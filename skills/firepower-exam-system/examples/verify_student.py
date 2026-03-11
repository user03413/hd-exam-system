"""
学号验证示例
演示如何调用学号验证接口
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:5000/api/exam"

def verify_student(student_id: str) -> dict:
    """
    验证学生学号
    
    Args:
        student_id: 学号（12位数字）
    
    Returns:
        dict: 验证结果，包含学生信息和会话ID
    """
    url = f"{BASE_URL}/verify"
    payload = {"student_id": student_id}
    
    response = requests.post(url, json=payload)
    return response.json()


def main():
    # 测试学号列表
    test_students = [
        "220252216068",  # 曾俊
        "220252216150",  # 吴萌
        "220252216186",  # 徐涛
        "000000000000",  # 不存在的学号
    ]
    
    for student_id in test_students:
        print(f"\n验证学号: {student_id}")
        print("-" * 40)
        
        result = verify_student(student_id)
        
        if result.get("success"):
            print(f"✓ 验证成功")
            print(f"  姓名: {result['student']['name']}")
            print(f"  专业: {result['student']['major']}")
            print(f"  会话ID: {result['session_id']}")
        else:
            print(f"✗ 验证失败: {result.get('message')}")


if __name__ == "__main__":
    main()
