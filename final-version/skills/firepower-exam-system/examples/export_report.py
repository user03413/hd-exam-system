"""
导出学习报告示例
演示如何导出PDF学习报告
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api/exam"


def run_full_exam_flow(student_id: str) -> dict:
    """运行完整考试流程并返回会话信息"""
    
    # 1. 验证学号
    print(f"验证学号: {student_id}")
    verify_result = requests.post(
        f"{BASE_URL}/verify",
        json={"student_id": student_id}
    ).json()
    
    if not verify_result.get("success"):
        raise Exception(f"验证失败: {verify_result.get('message')}")
    
    session_id = verify_result["session_id"]
    student_name = verify_result["student"]["name"]
    print(f"欢迎 {student_name}！")
    
    # 2. 开始考试
    print("\n开始考试...")
    start_result = requests.post(
        f"{BASE_URL}/start",
        json={"session_id": session_id}
    ).json()
    
    if not start_result.get("success"):
        raise Exception(f"开始考试失败: {start_result.get('message')}")
    
    questions = start_result["questions"]
    
    # 3. 构建答案
    answers = {}
    for q in questions:
        seq = str(q["seq"])
        if q["type"] == "单选题":
            answers[seq] = "A"
        elif q["type"] == "多选题":
            answers[seq] = ["A", "B"]
        else:
            answers[seq] = "测试答案内容"
    
    # 模拟答题时间
    time.sleep(3)
    
    # 4. 提交答案
    print("提交答案...")
    submit_result = requests.post(
        f"{BASE_URL}/submit",
        json={"session_id": session_id, "answers": answers}
    ).json()
    
    if not submit_result.get("success"):
        raise Exception(f"提交失败: {submit_result.get('message')}")
    
    return {
        "session_id": session_id,
        "student_name": student_name,
        "score": submit_result["score"],
        "results": submit_result["results"],
        "start_time": submit_result.get("start_time"),
        "end_time": submit_result.get("end_time"),
        "duration": submit_result.get("duration")
    }


def get_extension(question: str, chapter_title: str) -> str:
    """获取前沿拓展内容"""
    result = requests.post(
        f"{BASE_URL}/extension",
        json={"question": question, "chapter_title": chapter_title}
    ).json()
    
    if result.get("success"):
        return result.get("extension", "")
    return ""


def export_report(session_id: str, extensions: dict = None) -> str:
    """
    导出学习报告
    
    Args:
        session_id: 会话ID
        extensions: 前沿拓展内容（可选）
    
    Returns:
        str: PDF下载链接
    """
    result = requests.post(
        f"{BASE_URL}/export",
        json={
            "session_id": session_id,
            "extensions": extensions or {}
        }
    ).json()
    
    if result.get("success"):
        return result["download_url"]
    else:
        raise Exception(f"导出失败: {result.get('message')}")


def main():
    print("=" * 50)
    print("火电机组考核系统 - 导出学习报告示例")
    print("=" * 50)
    
    student_id = "220252216109"  # 宋文静
    
    try:
        # 1. 运行完整考试流程
        print(f"\n步骤1: 完成考试流程")
        print("-" * 40)
        exam_info = run_full_exam_flow(student_id)
        
        print(f"\n考试完成！")
        print(f"得分: {exam_info['score']} 分")
        print(f"用时: {exam_info['duration']}")
        
        # 2. 获取前沿拓展（可选）
        print(f"\n步骤2: 获取前沿拓展")
        print("-" * 40)
        
        extensions = {}
        for result in exam_info['results'][:2]:  # 只为前两题获取拓展
            print(f"获取第{result['seq']}题的拓展...")
            ext = get_extension(result['question'], result['chapter_title'])
            if ext:
                extensions[str(result['seq'])] = ext
                print(f"  ✓ 获取成功")
        
        # 3. 导出报告
        print(f"\n步骤3: 导出学习报告")
        print("-" * 40)
        
        pdf_url = export_report(exam_info['session_id'], extensions)
        
        print(f"\n{'=' * 50}")
        print("报告导出成功！")
        print("=" * 50)
        print(f"\n学生: {exam_info['student_name']}")
        print(f"得分: {exam_info['score']} 分")
        print(f"开始时间: {exam_info['start_time']}")
        print(f"结束时间: {exam_info['end_time']}")
        print(f"用时: {exam_info['duration']}")
        print(f"\nPDF下载链接:")
        print(pdf_url)
        
        print(f"\n提示: 链接有效期为24小时，请及时下载")
        
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
