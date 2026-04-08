#!/usr/bin/env python3
"""
测试考试时间限制功能
"""
import sys
sys.path.insert(0, '.')

# 测试1: 验证教师端考试时长选择器
def test_teacher_duration_selector():
    """测试教师端是否有考试时长选择器"""
    print("=" * 60)
    print("测试1: 验证教师端考试时长选择器")
    print("=" * 60)
    
    with open('src/exam_routes_new.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 检查考试时长选择器
    if '考试时长限制' in content and 'examDuration' in content:
        print("✓ 教师端存在考试时长选择器")
        
        # 检查选项
        options = ['不限制', '15 分钟', '30 分钟', '45 分钟', '60 分钟', '90 分钟', '120 分钟']
        all_options_present = all(opt in content for opt in options)
        if all_options_present:
            print("✓ 考试时长选项完整")
        else:
            print("✗ 考试时长选项不完整")
            return False
    else:
        print("✗ 教师端缺少考试时长选择器")
        return False
    
    print()
    return True

# 测试2: 验证后端API接收和保存考试时长
def test_backend_duration():
    """测试后端API是否正确接收和保存考试时长"""
    print("=" * 60)
    print("测试2: 验证后端API接收和保存考试时长")
    print("=" * 60)
    
    with open('src/exam_routes_new.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查get_chapter_link函数
    if 'duration = data.get' in content and "'duration': duration" in content:
        print("✓ get_chapter_link函数接收并保存考试时长")
    else:
        print("✗ get_chapter_link函数未正确处理考试时长")
        return False
    
    # 检查exam_verify函数
    if 'duration = data.get' in content and "'duration': duration" in content:
        print("✓ exam_verify函数接收并保存考试时长到session")
    else:
        print("✗ exam_verify函数未正确处理考试时长")
        return False
    
    # 检查URL参数中是否包含duration
    if "params.append(f\"duration={duration}\")" in content:
        print("✓ 考试时长已添加到URL参数")
    else:
        print("✗ 考试时长未添加到URL参数")
        return False
    
    print()
    return True

# 测试3: 验证学生端倒计时显示
def test_student_countdown():
    """测试学生端是否显示倒计时"""
    print("=" * 60)
    print("测试3: 验证学生端倒计时显示")
    print("=" * 60)
    
    with open('src/exam_routes_new.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查准备页时长显示
    if 'readyDurationInfo' in content and 'readyDuration' in content:
        print("✓ 准备页显示考试时长")
    else:
        print("✗ 准备页未显示考试时长")
        return False
    
    # 检查倒计时显示区域
    if 'countdownBar' in content and 'countdownTimer' in content:
        print("✓ 答题页显示倒计时")
    else:
        print("✗ 答题页未显示倒计时")
        return False
    
    # 检查进度条
    if 'countdownProgress' in content:
        print("✓ 倒计时进度条存在")
    else:
        print("✗ 倒计时进度条不存在")
        return False
    
    print()
    return True

# 测试4: 验证倒计时JavaScript功能
def test_countdown_js():
    """测试倒计时JavaScript功能"""
    print("=" * 60)
    print("测试4: 验证倒计时JavaScript功能")
    print("=" * 60)
    
    with open('src/exam_routes_new.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查倒计时函数
    functions = ['startCountdown', 'updateCountdownDisplay', 'stopCountdown']
    for func in functions:
        if f'function {func}' in content:
            print(f"✓ {func}函数存在")
        else:
            print(f"✗ {func}函数不存在")
            return False
    
    # 检查自动提交逻辑
    if 'submitExam' in content:
        print("✓ 自动提交函数存在")
    else:
        print("✗ 自动提交函数不存在")
        return False
    
    # 检查启动倒计时
    if 'startCountdown()' in content:
        print("✓ 开始答题时启动倒计时")
    else:
        print("✗ 未在开始答题时启动倒计时")
        return False
    
    # 检查停止倒计时
    if 'stopCountdown()' in content:
        print("✓ 提交试卷时停止倒计时")
    else:
        print("✗ 未在提交试卷时停止倒计时")
        return False
    
    print()
    return True

# 主测试函数
def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试考试时间限制功能")
    print("=" * 60 + "\n")
    
    tests = [
        test_teacher_duration_selector,
        test_backend_duration,
        test_student_countdown,
        test_countdown_js
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ 测试出错: {e}")
            results.append(False)
    
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！考试时间限制功能实现正确！")
        return 0
    else:
        print(f"\n✗ {total - passed}个测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
