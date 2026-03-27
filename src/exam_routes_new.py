"""火电机组考核系统 - 适配新版题库"""
import os
import json
import random
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from coze_coding_dev_sdk import SearchClient, DocumentGenerationClient
from coze_coding_utils.runtime_ctx.context import new_context

# 配置路径
WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
EXAM_CONFIG_FILE = os.path.join(WORKSPACE_PATH, 'assets', 'exam_config.json')
EXAM_RECORDS_FILE = os.path.join(WORKSPACE_PATH, 'assets', 'exam_records.json')


def load_exam_config() -> Dict:
    """加载考试配置"""
    default_config = {
        "question_bank": {"file": "assets/244题_热工自动化试题集.xlsx", "sheet_name": "244 题"},
        "student_list": {"file": "assets/火电机组考核学生名单.xlsx"},
        "exam_settings": {
            "question_count": 10,
            "single_choice_count": 4,
            "multiple_choice_count": 3,
            "short_answer_count": 3
        }
    }
    try:
        if os.path.exists(EXAM_CONFIG_FILE):
            with open(EXAM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
    except Exception as e:
        print(f"加载配置文件失败，使用默认配置: {e}")
    return default_config


# 加载配置
_exam_config = load_exam_config()
QUESTION_FILE = os.path.join(WORKSPACE_PATH, _exam_config['question_bank']['file'])
STUDENT_FILE = os.path.join(WORKSPACE_PATH, _exam_config['student_list']['file'])
QUESTION_SHEET_NAME = _exam_config['question_bank'].get('sheet_name', '244 题')

# 会话存储
exam_sessions: Dict[str, Dict] = {}

# 考试记录存储
exam_records: List[Dict] = []

# ============ 预生成试卷存储（统一试卷模式）============
# 结构: {link_id: {'questions': [...], 'chapter': 'xxx', 'mode': 'unified', 'created_at': datetime}}
exam_papers: Dict[str, Dict] = {}

# ============ 缓存机制（优化并发性能）============
_questions_cache: Optional[Dict[str, List]] = None  # 题库缓存
_students_cache: Optional[Dict[str, Dict]] = None   # 学生名单缓存
_cache_lock = {}  # 简单的锁机制（防止缓存穿透）


def load_exam_records() -> List[Dict]:
    """加载考试记录"""
    global exam_records
    try:
        if os.path.exists(EXAM_RECORDS_FILE):
            with open(EXAM_RECORDS_FILE, 'r', encoding='utf-8') as f:
                exam_records = json.load(f)
        return exam_records
    except Exception as e:
        print(f"加载考试记录失败: {e}")
        exam_records = []
        return exam_records


def save_exam_records():
    """保存考试记录"""
    try:
        with open(EXAM_RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(exam_records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存考试记录失败: {e}")


# 初始化加载考试记录
load_exam_records()


def load_students(use_cache: bool = True) -> Dict[str, Dict]:
    """加载学生名单 - 带缓存机制
    
    Args:
        use_cache: 是否使用缓存，默认True。设为False可强制刷新缓存。
    
    Returns:
        Dict[str, Dict]: 以学号为key的学生字典
    """
    global _students_cache
    
    # 如果缓存存在且要求使用缓存，直接返回
    if use_cache and _students_cache is not None:
        print("[缓存] 命中学生名单缓存")
        return _students_cache
    
    try:
        print(f"[缓存] {'刷新缓存' if _students_cache is not None else '首次加载'}学生名单...")
        
        df = pd.read_excel(STUDENT_FILE)
        students = {}
        for _, row in df.iterrows():
            student_id = str(int(row['学号'])).strip() if pd.notna(row['学号']) else ''
            if not student_id:
                continue
            students[student_id] = {
                'id': student_id,
                'name': str(row['姓名']).strip() if pd.notna(row['姓名']) else '',
                'major': str(row.get('专业', '控制工程')).strip()
            }
        
        # 添加测试账号（不影响真实学生数据）
        students['123456'] = {
            'id': '123456',
            'name': '测试学生',
            'major': '控制工程（测试）'
        }
        
        # 添加教师管理账号
        students['654321'] = {
            'id': '654321',
            'name': '教师管理员',
            'major': '教师',
            'is_teacher': True
        }
        
        # 存入缓存
        _students_cache = students
        
        print(f"[缓存] 学生名单加载完成: {len(students)}人")
        return students
    except Exception as e:
        print(f"加载学生名单失败: {e}")
        # 即使加载失败，也返回测试账号和教师账号
        return {
            '123456': {
                'id': '123456',
                'name': '测试学生',
                'major': '控制工程（测试）'
            },
            '654321': {
                'id': '654321',
                'name': '教师管理员',
                'major': '教师',
                'is_teacher': True
            }
        }


def parse_difficulty(diff_str: str) -> str:
    """从HTML中提取难度文本"""
    if pd.isna(diff_str):
        return '中等'
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', str(diff_str))
    return text.strip() if text.strip() else '中等'


def parse_options(option_str: str) -> Dict[str, str]:
    """解析选项字符串为字典"""
    options = {}
    if pd.isna(option_str) or not option_str:
        return options
    
    # 匹配 "A. xxx B. xxx C. xxx D. xxx" 格式
    pattern = r'([A-F])\.\s*([^A-F]+?)(?=\s*[A-F]\.|$)'
    matches = re.findall(pattern, str(option_str) + ' ')
    
    for letter, content in matches:
        options[letter.strip()] = content.strip()
    
    return options


def load_questions(use_cache: bool = True) -> Dict[str, List]:
    """加载题库 - 带缓存机制
    
    Args:
        use_cache: 是否使用缓存，默认True。设为False可强制刷新缓存。
    
    Returns:
        Dict[str, List]: 按题型分类的题目字典
    """
    global _questions_cache
    
    # 如果缓存存在且要求使用缓存，直接返回
    if use_cache and _questions_cache is not None:
        print("[缓存] 命中题库缓存")
        return _questions_cache
    
    try:
        print(f"[缓存] {'刷新缓存' if _questions_cache is not None else '首次加载'}题库...")
        
        df = pd.read_excel(QUESTION_FILE, sheet_name=QUESTION_SHEET_NAME)
        questions = {'单选题': [], '多选题': [], '简答题': []}
        
        for _, row in df.iterrows():
            q_type = str(row['题型']).strip()
            if q_type not in questions:
                continue
            
            difficulty = parse_difficulty(row.get('难度', '中等'))
            
            question = {
                'type': q_type,
                'id': int(row['题号']),
                'chapter': str(row['教材章节']).strip(),
                'page': str(row['页码']).strip() if pd.notna(row['页码']) else '',
                'question': str(row['题目']).strip(),
                'options': parse_options(row.get('选项', '')),
                'answer': str(row['答案']).strip(),
                'analysis': str(row['解析']).strip() if pd.notna(row['解析']) else '',
                'difficulty': difficulty
            }
            questions[q_type].append(question)
        
        # 存入缓存
        _questions_cache = questions
        
        print(f"[缓存] 题库加载完成: 单选{len(questions['单选题'])}题, 多选{len(questions['多选题'])}题, 简答{len(questions['简答题'])}题")
        return questions
    except Exception as e:
        print(f"加载题库失败: {e}")
        return {'单选题': [], '多选题': [], '简答题': []}


def generate_session_id(student_id: str) -> str:
    """生成会话ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{student_id}_{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def random_select_questions(all_questions: Dict, count: int = 10) -> List:
    """随机抽取题目 - 保证题型分布"""
    selected = []
    
    # 计算各题型数量
    single_count = min(4, len(all_questions['单选题']))
    multiple_count = min(3, len(all_questions['多选题']))
    short_count = count - single_count - multiple_count
    short_count = min(max(short_count, 3), len(all_questions['简答题']))
    
    # 随机抽取
    single_questions = random.sample(all_questions['单选题'], single_count)
    multiple_questions = random.sample(all_questions['多选题'], multiple_count)
    short_questions = random.sample(all_questions['简答题'], short_count)
    
    seq = 1
    for q in single_questions:
        q['seq'] = seq
        selected.append(q)
        seq += 1
    
    for q in multiple_questions:
        q['seq'] = seq
        selected.append(q)
        seq += 1
    
    for q in short_questions:
        q['seq'] = seq
        selected.append(q)
        seq += 1
    
    return selected


def calculate_score(questions: List, answers: Dict) -> tuple:
    """计算得分"""
    total_score = 0
    results = []
    
    for q in questions:
        q_type = q['type']
        q_id = q['seq']
        user_answer = answers.get(str(q_id), '')
        correct_answer = q['answer']
        
        is_correct = False
        score = 0
        
        if q_type == '单选题':
            if str(user_answer).upper() == str(correct_answer).upper():
                is_correct = True
                score = 10
        
        elif q_type == '多选题':
            # 多选题答案可能是 "ABC" 或 "A,B,C"
            user_set = set(str(user_answer).upper().replace(',', '').replace('，', '').replace(' ', ''))
            correct_set = set(str(correct_answer).upper().replace(',', '').replace('，', '').replace(' ', ''))
            if user_set == correct_set:
                is_correct = True
                score = 10
        
        elif q_type == '简答题':
            # 简答题基于关键词匹配
            user_text = str(user_answer).lower()
            correct_text = str(correct_answer).lower()
            analysis_text = str(q.get('analysis', '')).lower()
            
            # 合并答案和解析作为参考
            ref_text = correct_text + ' ' + analysis_text
            
            # 简单关键词匹配
            keywords = [w for w in re.findall(r'[\u4e00-\u9fa5]{2,}', ref_text) if len(w) >= 2][:10]
            if keywords:
                matched = sum(1 for kw in keywords if kw in user_text)
                match_ratio = matched / len(keywords)
                
                if match_ratio >= 0.5:
                    is_correct = True
                    score = 10
                elif match_ratio >= 0.3:
                    score = 5
        
        total_score += score
        
        results.append({
            'seq': q_id,
            'type': q_type,
            'question': q['question'],
            'options': q.get('options'),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'score': score,
            'analysis': q['analysis'],
            'chapter': q['chapter'],
            'page': q['page'],
            'difficulty': q['difficulty']
        })
    
    return total_score, results


def get_extension_content(question_text: str, chapter: str) -> str:
    """获取前沿拓展内容"""
    try:
        ctx = new_context(method="get_extension")
        search_client = SearchClient(ctx=ctx)
        
        search_query = f"火电厂热工自动控制 {chapter} 最新技术 行业案例"
        
        response = search_client.web_search(
            query=search_query,
            count=3,
            need_summary=True
        )
        
        content = "## 前沿拓展\n\n"
        
        if response.web_items:
            content += "### 相关资讯\n\n"
            for i, item in enumerate(response.web_items[:3], 1):
                content += f"**{i}. {item.title}**\n\n"
                if item.snippet:
                    content += f"{item.snippet}\n\n"
                content += f"🔗 [查看详情]({item.url})\n\n"
        
        if response.summary:
            content += f"### AI总结\n\n{response.summary}\n\n"
        
        return content
        
    except Exception as e:
        return f"## 前沿拓展\n\n暂无相关拓展信息。"


def generate_report(student_info: Dict, questions: List, results: List, total_score: int,
                    extensions: Dict, start_time: str = None, end_time: str = None, 
                    duration: str = None) -> str:
    """生成学习报告"""
    
    time_info = ""
    if start_time:
        time_info += f"| 开始时间 | {start_time} |\n"
    if end_time:
        time_info += f"| 结束时间 | {end_time} |\n"
    if duration:
        time_info += f"| 考试用时 | {duration} |\n"
    
    single_correct = sum(1 for r in results if r['type'] == '单选题' and r['is_correct'])
    multiple_correct = sum(1 for r in results if r['type'] == '多选题' and r['is_correct'])
    short_correct = sum(1 for r in results if r['type'] == '简答题' and r['is_correct'])
    single_score = sum(r['score'] for r in results if r['type'] == '单选题')
    multiple_score = sum(r['score'] for r in results if r['type'] == '多选题')
    short_score = sum(r['score'] for r in results if r['type'] == '简答题')
    
    report = f"""# 火电机组考核学习报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | {student_info['name']} |
| 学号 | {student_info['id']} |
| 专业 | {student_info.get('major', '控制工程')} |
{time_info}| 总分 | **{total_score}** / 100 分 |

## 成绩分析

| 题型 | 题数 | 正确 | 得分 |
|------|------|------|------|
| 单选题 | 4 | {single_correct} | {single_score} |
| 多选题 | 3 | {multiple_correct} | {multiple_score} |
| 简答题 | 3 | {short_correct} | {short_score} |

---

## 答题详情

"""
    
    for result in results:
        correct_mark = "✓ 正确" if result['is_correct'] else "✗ 错误"
        
        report += f"### 题目 {result['seq']}：{result['type']}（{result['difficulty']}）\n\n"
        report += f"**章节**：{result['chapter']}"
        if result['page']:
            report += f"（第{result['page']}页）"
        report += "\n\n"
        report += f"**题目**：{result['question']}\n\n"
        
        if result['options']:
            report += "**选项**：\n\n"
            for opt, content in result['options'].items():
                user_mark = "→ " if opt == result['user_answer'] else "  "
                correct_mark_opt = " ✓" if opt in result['correct_answer'] else ""
                report += f"{user_mark}**{opt}**. {content}{correct_mark_opt}\n\n"
        
        report += f"**你的答案**：{result['user_answer'] if result['user_answer'] else '未作答'}\n\n"
        report += f"**正确答案**：{result['correct_answer']}\n\n"
        report += f"**得分**：{result['score']} / 10 分\n\n"
        report += f"**解析**：\n\n{result['analysis']}\n\n"
        
        if str(result['seq']) in extensions:
            report += f"\n{extensions[str(result['seq'])]}\n\n"
        
        report += "---\n\n"
    
    wrong_questions = [r for r in results if not r['is_correct']]
    report += "## 学习建议\n\n"
    if wrong_questions:
        report += "建议重点复习以下内容：\n\n"
        for r in wrong_questions:
            report += f"- {r['chapter']}：{r['question'][:40]}...\n"
    else:
        report += "恭喜！全部答对，继续保持！\n"
    
    report += f"\n---\n\n*本报告由火电机组考核系统自动生成*\n"
    
    return report


# ============== HTML 页面模板 ==============

EXAM_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>火电机组考核系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary: #1a73e8;
            --success: #34a853;
            --danger: #ea4335;
            --warning: #fbbc04;
            --bg: #f8f9fa;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, #1557b0 100%);
            color: white;
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 1.25rem; margin: 0; }
        .header .sub { font-size: 0.8rem; opacity: 0.9; }
        .container { max-width: 800px; margin: 0 auto; padding: 15px; }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 15px;
            border: none;
        }
        .card-body { padding: 20px; }
        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 500;
        }
        .btn-primary:hover { background: #1557b0; }
        .btn-success { background: var(--success); border: none; }
        .form-control {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px 15px;
            font-size: 16px;
        }
        .form-control:focus { border-color: var(--primary); box-shadow: none; }
        
        /* 题目卡片 */
        .q-card {
            background: white;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 15px;
            border-left: 4px solid var(--primary);
        }
        .q-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .q-type {
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 500;
        }
        .type-单选 { background: #e3f2fd; color: #1565c0; }
        .type-多选 { background: #fff3e0; color: #e65100; }
        .type-简答 { background: #e8f5e9; color: #2e7d32; }
        .diff-基础 { color: var(--success); }
        .diff-中等 { color: var(--warning); }
        .diff-困难 { color: var(--danger); }
        .q-text { font-size: 15px; line-height: 1.6; margin-bottom: 12px; }
        .q-chapter { font-size: 12px; color: #666; margin-bottom: 8px; }
        
        /* 选项 */
        .opt {
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .opt:hover { border-color: var(--primary); background: #f0f7ff; }
        .opt.sel { border-color: var(--primary); background: #e3f2fd; }
        .opt.ok { border-color: var(--success); background: #e8f5e9; }
        .opt.err { border-color: var(--danger); background: #ffebee; }
        .opt label { cursor: pointer; display: flex; align-items: flex-start; margin: 0; }
        .opt input { margin: 4px 10px 0 0; }
        .opt-letter { font-weight: 600; color: var(--primary); margin-right: 8px; }
        
        /* 简答题输入 */
        .short-input {
            width: 100%;
            min-height: 100px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            resize: vertical;
        }
        .short-input:focus { border-color: var(--primary); outline: none; }
        
        /* 结果页 */
        .score-box {
            background: linear-gradient(135deg, var(--primary) 0%, #1557b0 100%);
            color: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            margin-bottom: 20px;
        }
        .score-num { font-size: 48px; font-weight: 700; }
        .score-label { font-size: 14px; opacity: 0.9; }
        .stats { display: flex; justify-content: center; gap: 30px; margin-top: 15px; }
        .stat { text-align: center; }
        .stat-v { font-size: 24px; font-weight: 600; }
        .stat-l { font-size: 12px; opacity: 0.8; }
        
        /* 解析框 */
        .analysis {
            background: #f0f7ff;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            border: 1px solid #bbdefb;
        }
        .analysis h6 { color: #1565c0; margin: 0 0 8px 0; font-size: 13px; }
        
        /* 拓展框 */
        .ext {
            background: #fff8e1;
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
            border: 1px solid #ffe082;
        }
        .ext h6 { color: #f57c00; margin: 0 0 8px 0; font-size: 13px; }
        
        /* 进度条 */
        .progress-bar {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: var(--primary);
            border-radius: 3px;
            transition: width 0.3s;
        }
        
        /* 计时器 */
        .timer { font-size: 18px; font-weight: 600; }
        
        /* 隐藏/显示 */
        .section { display: none; }
        .section.active { display: block; }
        
        /* 移动端适配 */
        @media (max-width: 576px) {
            .container { padding: 10px; }
            .card-body { padding: 15px; }
            .q-card { padding: 12px; }
            .score-num { font-size: 36px; }
            .btn-primary { width: 100%; }
            .stats { gap: 15px; }
        }
        
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #fff;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1><i class="bi bi-lightning-charge"></i> 火电机组考核系统</h1>
            <div class="sub" id="examTitle">热工自动化在线考试</div>
        </div>
    </div>
    
    <div class="container">
        <!-- 登录页 -->
        <div id="loginSec" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <div style="width:80px;height:80px;background:linear-gradient(135deg,var(--primary),#1557b0);border-radius:50%;margin:0 auto 20px;display:flex;align-items:center;justify-content:center;">
                        <i class="bi bi-person" style="font-size:40px;color:white;"></i>
                    </div>
                    <h5>考生身份验证</h5>
                    <div id="loginChapterInfo" class="alert alert-primary mb-3" style="display:none;">
                        <i class="bi bi-book me-2"></i><strong>本次考试章节：</strong><span id="loginChapter"></span>
                    </div>
                    <p class="text-muted small mb-4">请输入学号进入考试</p>
                    <form id="loginForm">
                        <input type="text" class="form-control mb-3" id="studentId" placeholder="请输入学号" required autocomplete="off">
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="bi bi-box-arrow-in-right me-2"></i>验证并进入
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <!-- 准备页 -->
        <div id="readySec" class="section">
            <div class="card">
                <div class="card-body">
                    <div class="alert alert-success">
                        <h5 class="mb-2">验证成功</h5>
                        <p class="mb-1"><strong>姓名：</strong><span id="sName"></span></p>
                        <p class="mb-1"><strong>学号：</strong><span id="sId"></span></p>
                        <p class="mb-0"><strong>专业：</strong><span id="sMajor"></span></p>
                    </div>
                    <div id="readyChapterInfo" class="alert alert-primary" style="display:none;">
                        <i class="bi bi-book me-2"></i><strong>考试章节：</strong><span id="readyChapter"></span>
                    </div>
                    <div class="alert alert-info small">
                        <strong>考试说明：</strong><br>
                        • 共10道题（单选4题 + 多选3题 + 简答3题）<br>
                        • 每题10分，满分100分<br>
                        • 提交后可查看解析和前沿拓展
                    </div>
                    <button id="startBtn" class="btn btn-primary w-100">
                        <i class="bi bi-play-circle me-2"></i>开始答题
                    </button>
                </div>
            </div>
        </div>
        
        <!-- 答题页 -->
        <div id="examSec" class="section">
            <div class="card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span id="progTxt">0 / 10</span>
                        <span class="timer" id="timer">00:00</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progBar" style="width:0%"></div>
                    </div>
                    <div id="qList"></div>
                    <div class="text-center mt-4">
                        <button id="submitBtn" class="btn btn-primary">
                            <i class="bi bi-check-circle me-2"></i>提交答卷
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 结果页 -->
        <div id="resultSec" class="section">
            <div class="card">
                <div class="card-body">
                    <div class="score-box">
                        <div class="score-num" id="scoreNum">0</div>
                        <div class="score-label">分</div>
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-v" id="okCnt">0</div>
                                <div class="stat-l">正确</div>
                            </div>
                            <div class="stat">
                                <div class="stat-v" id="partCnt" style="color:#ffeb3b">0</div>
                                <div class="stat-l">部分</div>
                            </div>
                            <div class="stat">
                                <div class="stat-v" id="errCnt" style="color:#ffcdd2">0</div>
                                <div class="stat-l">错误</div>
                            </div>
                        </div>
                    </div>
                    <div class="text-center mb-3">
                        <span class="badge bg-light text-dark" id="timeInfo"></span>
                    </div>
                    <p class="text-center text-muted mb-4" id="scoreComment"></p>
                    <div id="resultList"></div>
                    <div class="text-center mt-4 pt-3 border-top">
                        <button id="exportBtn" class="btn btn-success me-2 mb-2">
                            <i class="bi bi-download me-2"></i>导出报告
                        </button>
                        <button id="restartBtn" class="btn btn-outline-secondary mb-2">
                            <i class="bi bi-arrow-repeat me-2"></i>重新开始
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 读取URL参数中的章节信息
        const urlParams = new URLSearchParams(window.location.search);
        const chapterParam = urlParams.get('chapter');
        const linkIdParam = urlParams.get('linkId');
        const modeParam = urlParams.get('mode') || 'random'; // 考试模式，默认随机
        
        let sessionId = null, questions = [], answers = {}, extensions = {}, timer = null, seconds = 0;
        let currentChapter = chapterParam || ''; // 当前考试章节
        let currentMode = modeParam; // 当前考试模式
        let currentLinkId = linkIdParam || ''; // 当前链接ID
        
        // 页面加载时立即显示章节信息（如果有）
        if (currentChapter) {
            document.getElementById('examTitle').textContent = currentChapter + ' - 热工自动化在线考试';
            // 在登录页显示章节信息
            document.getElementById('loginChapter').textContent = currentChapter;
            document.getElementById('loginChapterInfo').style.display = 'block';
        }
        
        // 如果是统一试卷模式，在登录页显示提示
        if (currentMode === 'unified') {
            const modeInfo = document.createElement('div');
            modeInfo.className = 'alert alert-warning small mt-2 mb-0';
            modeInfo.innerHTML = '<i class="bi bi-info-circle me-1"></i>统一试卷模式：所有同学题目相同';
            document.getElementById('loginChapterInfo').parentNode.appendChild(modeInfo);
        }
        
        function show(secId) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(secId).classList.add('active');
        }
        
        function tick() {
            seconds++;
            const m = String(Math.floor(seconds / 60)).padStart(2, '0');
            const s = String(seconds % 60).padStart(2, '0');
            document.getElementById('timer').textContent = m + ':' + s;
        }
        
        function updateProg() {
            const n = Object.keys(answers).length;
            document.getElementById('progTxt').textContent = n + ' / ' + questions.length;
            document.getElementById('progBar').style.width = (n / questions.length * 100) + '%';
        }
        
        function renderQ() {
            const c = document.getElementById('qList');
            c.innerHTML = '';
            questions.forEach(q => {
                const div = document.createElement('div');
                div.className = 'q-card';
                div.id = 'q-' + q.seq;
                
                const typeCls = q.type === '单选题' ? 'type-单选' : q.type === '多选题' ? 'type-多选' : 'type-简答';
                const diffCls = 'diff-' + q.difficulty;
                
                let optHtml = '';
                if (q.type === '单选题' || q.type === '多选题') {
                    optHtml = '<div>';
                    Object.entries(q.options || {}).forEach(([k, v]) => {
                        const inp = q.type === '单选题' ? 'radio' : 'checkbox';
                        optHtml += '<div class="opt" data-seq="' + q.seq + '" data-opt="' + k + '"><label><input type="' + inp + '" name="q' + q.seq + '" value="' + k + '"><span class="opt-letter">' + k + '.</span><span>' + v + '</span></label></div>';
                    });
                    optHtml += '</div>';
                } else {
                    optHtml = '<textarea class="short-input" data-seq="' + q.seq + '" placeholder="请输入答案..."></textarea>';
                }
                
                div.innerHTML = '<div class="q-header"><span><span class="q-type ' + typeCls + '">' + q.type + '</span> <span class="' + diffCls + '">' + q.difficulty + '</span></span><span class="text-muted small">第' + q.seq + '题</span></div><div class="q-chapter"><i class="bi bi-book"></i> ' + q.chapter + (q.page ? '（第' + q.page + '页）' : '') + '</div><div class="q-text"><strong>' + q.seq + '、</strong>' + q.question + '</div>' + optHtml;
                c.appendChild(div);
            });
            bindOpt();
        }
        
        function bindOpt() {
            document.querySelectorAll('.opt').forEach(o => {
                o.addEventListener('click', function() {
                    const seq = this.dataset.seq;
                    const opt = this.dataset.opt;
                    const inp = this.querySelector('input');
                    const q = questions.find(x => x.seq == seq);
                    
                    if (q.type === '单选题') {
                        document.querySelectorAll('[data-seq="' + seq + '"]').forEach(x => x.classList.remove('sel'));
                        this.classList.add('sel');
                        inp.checked = true;
                        answers[seq] = opt;
                    } else {
                        this.classList.toggle('sel');
                        inp.checked = !inp.checked;
                        const sel = [];
                        document.querySelectorAll('[data-seq="' + seq + '"].sel').forEach(x => sel.push(x.dataset.opt));
                        answers[seq] = sel;
                    }
                    updateProg();
                });
            });
            
            document.querySelectorAll('.short-input').forEach(t => {
                t.addEventListener('input', function() {
                    answers[this.dataset.seq] = this.value.trim();
                    updateProg();
                });
            });
        }
        
        function renderResult(results) {
            const c = document.getElementById('resultList');
            c.innerHTML = '';
            results.forEach(r => {
                const div = document.createElement('div');
                div.className = 'q-card';
                
                const icon = r.is_correct ? '✓' : (r.score > 0 ? '△' : '✗');
                const cls = r.is_correct ? 'text-success' : (r.score > 0 ? 'text-warning' : 'text-danger');
                
                let optHtml = '';
                if (r.options) {
                    optHtml = '<div>';
                    Object.entries(r.options).forEach(([k, v]) => {
                        const uSel = (Array.isArray(r.user_answer) ? r.user_answer.includes(k) : r.user_answer === k);
                        const isOk = r.correct_answer.includes(k);
                        let cls = '';
                        if (isOk) cls = 'ok';
                        else if (uSel) cls = 'err';
                        const mark = isOk ? ' ✓' : (uSel ? ' ✗' : '');
                        optHtml += '<div class="opt ' + cls + '"><span class="opt-letter">' + k + '.</span><span>' + v + mark + '</span></div>';
                    });
                    optHtml += '</div>';
                }
                
                const ua = Array.isArray(r.user_answer) ? r.user_answer.join('') : r.user_answer;
                const ca = r.correct_answer;
                
                let ansHtml = r.type === '简答题' 
                    ? '<div class="alert alert-light mt-2"><strong>你的答案：</strong>' + (ua || '未作答') + '<br><strong>参考答案：</strong>' + ca + '</div>'
                    : '<p class="mt-2 small"><strong>你的答案：</strong>' + (ua || '未作答') + ' &nbsp; <strong>正确答案：</strong>' + ca + '</p>';
                
                div.innerHTML = '<div class="q-header"><span><span class="q-type type-' + (r.type === '单选题' ? '单选' : r.type === '多选题' ? '多选' : '简答') + '">' + r.type + '</span> <span class="' + cls + '">' + icon + '</span></span><span class="fw-bold">' + r.score + '/10分</span></div><div class="q-chapter">' + r.chapter + '</div><div class="q-text"><strong>' + r.seq + '、</strong>' + r.question + '</div>' + optHtml + ansHtml + '<div class="analysis"><h6><i class="bi bi-lightbulb"></i> 解析</h6><p class="mb-0 small">' + r.analysis + '</p></div><div class="ext" id="ext-' + r.seq + '"><h6><i class="bi bi-search"></i> 前沿拓展</h6><button class="btn btn-sm btn-outline-warning" onclick="loadExt(' + r.seq + ')">点击加载</button></div>';
                c.appendChild(div);
            });
        }
        
        async function loadExt(seq) {
            const div = document.getElementById('ext-' + seq);
            div.innerHTML = '<span class="loading"></span> 加载中...';
            const q = questions.find(x => x.seq === seq);
            try {
                const res = await fetch('/api/exam/extension', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: q.question, chapter: q.chapter})
                });
                const data = await res.json();
                if (data.success) {
                    extensions[seq] = data.extension;
                    div.innerHTML = '<h6><i class="bi bi-search"></i> 前沿拓展</h6><div class="small">' + data.extension.replace(/\\n/g, '<br>') + '</div>';
                } else {
                    div.innerHTML = '<p class="text-muted small mb-0">' + data.message + '</p>';
                }
            } catch(e) {
                div.innerHTML = '<p class="text-danger small mb-0">加载失败</p>';
            }
        }
        
        async function api(endpoint, data) {
            const res = await fetch('/api/exam' + endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            return res.json();
        }
        
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const id = document.getElementById('studentId').value.trim();
            if (!id) return alert('请输入学号');
            
            const btn = this.querySelector('button');
            btn.disabled = true;
            btn.innerHTML = '<span class="loading me-2"></span>验证中...';
            
            try {
                const r = await api('/verify', {
                    student_id: id, 
                    chapter: currentChapter,
                    linkId: currentLinkId,
                    mode: currentMode
                });
                if (r.success) {
                    // 如果是教师账号，跳转到教师管理页面
                    if (r.student.is_teacher) {
                        window.location.href = '/teacher';
                        return;
                    }
                    sessionId = r.session_id;
                    document.getElementById('sName').textContent = r.student.name;
                    document.getElementById('sId').textContent = r.student.id;
                    document.getElementById('sMajor').textContent = r.student.major;
                    
                    // 显示考试章节（在标题、准备页都要显示）
                    if (r.chapter) {
                        currentChapter = r.chapter; // 更新章节信息
                        document.getElementById('examTitle').textContent = r.chapter + ' - 热工自动化在线考试';
                        document.getElementById('readyChapter').textContent = r.chapter;
                        document.getElementById('readyChapterInfo').style.display = 'block';
                    }
                    
                    // 如果是统一试卷模式，在准备页显示提示
                    if (r.exam_mode === 'unified') {
                        const modeAlert = document.createElement('div');
                        modeAlert.className = 'alert alert-warning small';
                        modeAlert.innerHTML = '<i class="bi bi-info-circle me-1"></i>' + (r.exam_mode_text || '统一试卷模式：所有同学题目相同');
                        document.getElementById('readyChapterInfo').parentNode.insertBefore(modeAlert, document.getElementById('readyChapterInfo').nextSibling);
                    }
                    
                    show('readySec');
                } else {
                    alert(r.message);
                }
            } catch(e) {
                alert('验证失败：' + e.message);
            }
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-box-arrow-in-right me-2"></i>验证并进入';
        });
        
        document.getElementById('startBtn').addEventListener('click', async function() {
            this.disabled = true;
            this.innerHTML = '<span class="loading me-2"></span>加载题目...';
            
            try {
                const r = await api('/start', {session_id: sessionId});
                if (r.success) {
                    questions = r.questions;
                    renderQ();
                    show('examSec');
                    timer = setInterval(tick, 1000);
                } else {
                    alert(r.message);
                }
            } catch(e) {
                alert('加载失败：' + e.message);
            }
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-play-circle me-2"></i>开始答题';
        });
        
        document.getElementById('submitBtn').addEventListener('click', async function() {
            if (Object.keys(answers).length < questions.length && !confirm('还有题目未作答，确定提交吗？')) return;
            
            this.disabled = true;
            this.innerHTML = '<span class="loading me-2"></span>提交中...';
            
            try {
                clearInterval(timer);
                const r = await api('/submit', {session_id: sessionId, answers: answers});
                
                if (r.success) {
                    document.getElementById('scoreNum').textContent = r.score;
                    
                    let ok = 0, part = 0, err = 0;
                    r.results.forEach(x => { if (x.is_correct) ok++; else if (x.score > 0) part++; else err++; });
                    document.getElementById('okCnt').textContent = ok;
                    document.getElementById('partCnt').textContent = part;
                    document.getElementById('errCnt').textContent = err;
                    
                    const comment = r.score >= 90 ? '优秀！继续保持！' : r.score >= 80 ? '良好，再接再厉！' : r.score >= 60 ? '及格，需加强学习。' : '不及格，请认真复习。';
                    document.getElementById('scoreComment').textContent = comment;
                    
                    document.getElementById('timeInfo').innerHTML = '<i class="bi bi-clock"></i> 用时 ' + (r.duration || '--') + ' | ' + (r.start_time || '') + ' ~ ' + (r.end_time || '');
                    
                    renderResult(r.results);
                    show('resultSec');
                } else {
                    alert(r.message);
                }
            } catch(e) {
                alert('提交失败：' + e.message);
            }
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-check-circle me-2"></i>提交答卷';
        });
        
        document.getElementById('exportBtn').addEventListener('click', async function() {
            this.disabled = true;
            this.innerHTML = '<span class="loading me-2"></span>生成中...';
            
            try {
                const r = await api('/export', {session_id: sessionId, extensions: extensions});
                if (r.success) {
                    window.open(r.download_url, '_blank');
                    alert('报告已生成！');
                } else {
                    alert(r.message);
                }
            } catch(e) {
                alert('导出失败：' + e.message);
            }
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-download me-2"></i>导出报告';
        });
        
        document.getElementById('restartBtn').addEventListener('click', function() {
            if (confirm('确定重新开始？')) location.reload();
        });
    </script>
</body>
</html>
'''


# ============== API 处理函数 ==============

async def exam_verify(request: Request) -> JSONResponse:
    """验证学号
    
    参数：
    - student_id: 学号
    - chapter: 章节参数（可选）
    - linkId: 链接ID（可选，用于统一试卷模式）
    - mode: 考试模式（可选，unified/random）
    """
    try:
        data = await request.json()
        student_id = str(data.get('student_id', '')).strip()
        chapter = data.get('chapter', '')  # 接收章节参数
        link_id = data.get('linkId', '')   # 接收链接ID
        mode = data.get('mode', 'random')  # 接收考试模式
        
        if not student_id:
            return JSONResponse({'success': False, 'message': '请输入学号'})
        
        students = load_students()
        
        if student_id not in students:
            return JSONResponse({'success': False, 'message': '学号不存在，请检查输入'})
        
        student = students[student_id]
        session_id = generate_session_id(student_id)
        
        exam_sessions[session_id] = {
            'student': student,
            'chapter': chapter,      # 保存章节参数到session
            'linkId': link_id,       # 保存链接ID到session
            'mode': mode,            # 保存考试模式到session
            'questions': None,
            'answers': {},
            'start_time': datetime.now().isoformat()
        }
        
        response_data = {
            'success': True,
            'message': f"验证成功，欢迎 {student['name']} 同学！",
            'student': student,
            'session_id': session_id
        }
        
        # 如果有章节信息，返回给前端显示
        if chapter:
            response_data['chapter'] = chapter
        
        # 如果是统一试卷模式，提示用户
        if mode == 'unified':
            response_data['exam_mode'] = 'unified'
            response_data['exam_mode_text'] = '统一试卷模式（所有同学题目相同）'
        
        return JSONResponse(response_data)
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'验证失败：{str(e)}'})


def filter_questions_by_chapter(all_questions: Dict, chapter: str) -> Dict:
    """根据章节筛选题目"""
    if not chapter:
        return all_questions
    
    filtered = {'单选题': [], '多选题': [], '简答题': []}
    
    for q_type in ['单选题', '多选题', '简答题']:
        for q in all_questions[q_type]:
            # 章节匹配：支持"第一章"、"第一章 基础知识"等多种格式
            q_chapter = q.get('chapter', '')
            # 提取章节号（如"第一章"、"第九章"等）
            chapter_match = re.search(r'第([一二三四五六七八九十百]+)章', chapter)
            q_chapter_match = re.search(r'第([一二三四五六七八九十百]+)章', q_chapter)
            
            if chapter_match and q_chapter_match:
                # 比较章节号
                if chapter_match.group(1) == q_chapter_match.group(1):
                    filtered[q_type].append(q)
            elif chapter in q_chapter or q_chapter in chapter:
                # 简单包含匹配
                filtered[q_type].append(q)
    
    print(f"章节筛选: {chapter} -> 单选{len(filtered['单选题'])}题, 多选{len(filtered['多选题'])}题, 简答{len(filtered['简答题'])}题")
    return filtered


async def exam_start(request: Request) -> JSONResponse:
    """开始考试
    
    支持两种模式：
    - unified（统一试卷）：使用预生成的试卷，所有学生题目相同
    - random（随机试卷）：每个学生独立随机抽题
    """
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in exam_sessions:
            return JSONResponse({'success': False, 'message': '会话无效，请重新登录'})
        
        session = exam_sessions[session_id]
        chapter = session.get('chapter', '')  # 从session中获取章节参数
        mode = session.get('mode', 'random')  # 从session中获取考试模式
        link_id = session.get('linkId', '')   # 从session中获取链接ID
        
        # 判断考试模式
        if mode == 'unified' and link_id and link_id in exam_papers:
            # 统一试卷模式：使用预生成的试卷
            paper = exam_papers[link_id]
            selected_questions = paper['questions']
            print(f"[统一试卷] 学生 {session['student']['name']} 使用预生成试卷 linkId={link_id}")
        else:
            # 随机试卷模式：独立随机抽题
            all_questions = load_questions()
            
            # 如果有章节参数，筛选题目
            if chapter:
                all_questions = filter_questions_by_chapter(all_questions, chapter)
                
                # 检查筛选后的题目数量
                total_questions = len(all_questions['单选题']) + len(all_questions['多选题']) + len(all_questions['简答题'])
                if total_questions < 10:
                    return JSONResponse({
                        'success': False, 
                        'message': f'该章节题目数量不足（仅{total_questions}题），无法生成试卷'
                    })
            
            selected_questions = random_select_questions(all_questions, 10)
            print(f"[随机试卷] 学生 {session['student']['name']} 随机抽题 章节={chapter or '全题库'}")
        
        start_time = datetime.now()
        exam_sessions[session_id]['questions'] = selected_questions
        exam_sessions[session_id]['start_time_obj'] = start_time
        
        questions_for_client = []
        for q in selected_questions:
            questions_for_client.append({
                'seq': q['seq'],
                'type': q['type'],
                'question': q['question'],
                'options': q.get('options'),
                'chapter': q['chapter'],
                'page': q['page'],
                'difficulty': q['difficulty']
            })
        
        response_data = {
            'success': True,
            'questions': questions_for_client,
            'total': len(questions_for_client),
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'exam_mode': mode  # 返回考试模式
        }
        
        # 如果有章节信息，返回给前端
        if chapter:
            response_data['chapter'] = chapter
        
        return JSONResponse(response_data)
        
    except Exception as e:
        print(f"开始考试失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'开始考试失败：{str(e)}'})


async def exam_submit(request: Request) -> JSONResponse:
    """提交答案"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        answers = data.get('answers', {})
        
        if not session_id or session_id not in exam_sessions:
            return JSONResponse({'success': False, 'message': '会话无效'})
        
        session = exam_sessions[session_id]
        questions = session['questions']
        student = session.get('student', {})
        
        if not questions:
            return JSONResponse({'success': False, 'message': '未获取题目'})
        
        total_score, results = calculate_score(questions, answers)
        
        end_time = datetime.now()
        start_time_obj = session.get('start_time_obj', end_time)
        duration_seconds = int((end_time - start_time_obj).total_seconds())
        
        exam_sessions[session_id]['answers'] = answers
        exam_sessions[session_id]['results'] = results
        exam_sessions[session_id]['total_score'] = total_score
        exam_sessions[session_id]['end_time_obj'] = end_time
        exam_sessions[session_id]['duration_seconds'] = duration_seconds
        
        # 保存考试记录（排除教师账号）
        if not student.get('is_teacher'):
            record = {
                'student_id': student.get('id', ''),
                'student_name': student.get('name', ''),
                'major': student.get('major', ''),
                'score': total_score,
                'duration_seconds': duration_seconds,
                'start_time': start_time_obj.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': results
            }
            exam_records.append(record)
            save_exam_records()
        
        return JSONResponse({
            'success': True,
            'score': total_score,
            'results': results,
            'start_time': start_time_obj.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': f'{duration_seconds // 60}分{duration_seconds % 60}秒'
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'提交失败：{str(e)}'})


async def exam_extension(request: Request) -> JSONResponse:
    """获取前沿拓展"""
    try:
        data = await request.json()
        question = data.get('question', '')
        chapter = data.get('chapter', '')
        
        extension = get_extension_content(question, chapter)
        
        return JSONResponse({
            'success': True,
            'extension': extension
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'获取拓展失败：{str(e)}'})


async def exam_export(request: Request) -> JSONResponse:
    """导出学习报告"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        extensions = data.get('extensions', {})
        
        if not session_id or session_id not in exam_sessions:
            return JSONResponse({'success': False, 'message': '会话无效'})
        
        session = exam_sessions[session_id]
        
        start_time = session.get('start_time_obj')
        end_time = session.get('end_time_obj')
        duration_seconds = session.get('duration_seconds', 0)
        
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None
        duration_str = f"{duration_seconds // 60}分{duration_seconds % 60}秒" if duration_seconds else None
        
        report_content = generate_report(
            session['student'],
            session['questions'],
            session['results'],
            session['total_score'],
            extensions,
            start_time_str,
            end_time_str,
            duration_str
        )
        
        client = DocumentGenerationClient()
        title = f"exam_report_{session['student']['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        pdf_url = client.create_pdf_from_markdown(report_content, title)
        
        return JSONResponse({
            'success': True,
            'download_url': pdf_url,
            'message': '报告生成成功'
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'导出失败：{str(e)}'})


def get_exam_page() -> HTMLResponse:
    """返回考核页面"""
    return HTMLResponse(content=EXAM_HTML)


# ============== 教师管理功能 ==============

TEACHER_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>教师管理后台 - 火电机组考核系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root{--primary:#1a73e8;--success:#34a853;--danger:#ea4335;--warning:#fbbc04;--bg:#f8f9fa}
        *{box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);margin:0;min-height:100vh}
        .header{background:linear-gradient(135deg,#34a853 0%,#2d8a47 100%);color:white;padding:15px 0;position:sticky;top:0;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        .header h1{font-size:1.25rem;margin:0}
        .container{max-width:1200px;margin:0 auto;padding:15px}
        .card{background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:15px;border:none}
        .card-body{padding:20px}
        .btn-primary{background:var(--primary);border:none;border-radius:8px;padding:12px 24px;font-weight:500}
        .btn-success{background:var(--success);border:none}
        .stat-card{background:linear-gradient(135deg,var(--primary),#1557b0);color:white;border-radius:12px;padding:20px;text-align:center}
        .stat-num{font-size:36px;font-weight:700}
        .stat-label{font-size:14px;opacity:0.9}
        .table{margin-bottom:0}
        .table th{background:#f8f9fa;border-bottom:2px solid #dee2e6}
        .score-high{color:var(--success);font-weight:600}
        .score-mid{color:var(--warning);font-weight:600}
        .score-low{color:var(--danger);font-weight:600}
        .section{display:none}
        .section.active{display:block}
        @media(max-width:576px){.container{padding:10px}.stat-num{font-size:28px}}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1><i class="bi bi-person-badge"></i> 教师管理后台</h1>
            <div class="sub">学生学习情况统计</div>
        </div>
    </div>
    
    <div class="container">
        <!-- 登录 -->
        <div id="loginSec" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <div style="width:80px;height:80px;background:linear-gradient(135deg,#34a853,#2d8a47);border-radius:50%;margin:0 auto 20px;display:flex;align-items:center;justify-content:center">
                        <i class="bi bi-shield-lock" style="font-size:40px;color:white"></i>
                    </div>
                    <h5>教师登录</h5>
                    <p class="text-muted small">请输入教师工号登录</p>
                    <form id="loginForm">
                        <input type="text" class="form-control mb-3" id="teacherId" placeholder="教师工号" required autocomplete="off">
                        <button type="submit" class="btn btn-success w-100"><i class="bi bi-box-arrow-in-right me-2"></i>登录</button>
                    </form>
                </div>
            </div>
        </div>
        
        <!-- 统计面板 -->
        <div id="statsSec" class="section">
            <!-- 统计卡片 -->
            <div class="row mb-4">
                <div class="col-6 col-md-3 mb-3">
                    <div class="stat-card">
                        <div class="stat-num" id="totalStudents">0</div>
                        <div class="stat-label">学生总数</div>
                    </div>
                </div>
                <div class="col-6 col-md-3 mb-3">
                    <div class="stat-card" style="background:linear-gradient(135deg,#34a853,#2d8a47)">
                        <div class="stat-num" id="examinedCount">0</div>
                        <div class="stat-label">已考试人数</div>
                    </div>
                </div>
                <div class="col-6 col-md-3 mb-3">
                    <div class="stat-card" style="background:linear-gradient(135deg,#fbbc04,#e6a800)">
                        <div class="stat-num" id="avgScore">0</div>
                        <div class="stat-label">平均分</div>
                    </div>
                </div>
                <div class="col-6 col-md-3 mb-3">
                    <div class="stat-card" style="background:linear-gradient(135deg,#ea4335,#c5221f)">
                        <div class="stat-num" id="passRate">0%</div>
                        <div class="stat-label">及格率</div>
                    </div>
                </div>
            </div>
            
            <!-- 章节出题功能 -->
            <div class="card mb-4">
                <div class="card-body">
                    <h5 class="mb-3"><i class="bi bi-book-half me-2"></i>章节出题</h5>
                    <p class="text-muted small mb-3">选择章节生成专属考试链接，学生通过该链接只能考所选章节的题目</p>
                    
                    <div class="mb-3">
                        <label class="form-label">选择章节</label>
                        <select class="form-select" id="chapterSelect">
                            <option value="">-- 全题库（不限制章节）--</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">考试模式</label>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="examMode" id="modeUnified" value="unified">
                            <label class="form-check-label" for="modeUnified">
                                <strong>统一试卷</strong> <span class="text-muted small">（推荐正式考试）</span>
                            </label>
                            <div class="text-muted small ms-4">所有学生题目相同，便于讲评和存档</div>
                        </div>
                        <div class="form-check mt-2">
                            <input class="form-check-input" type="radio" name="examMode" id="modeRandom" value="random" checked>
                            <label class="form-check-label" for="modeRandom">
                                <strong>随机试卷</strong> <span class="text-muted small">（推荐平时练习）</span>
                            </label>
                            <div class="text-muted small ms-4">每位学生题目随机，增加练习覆盖面</div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateChapterLink()">
                        <i class="bi bi-link-45deg me-2"></i>生成考试链接
                    </button>
                    
                    <div id="linkDisplay" class="mt-3" style="display:none">
                        <div class="alert alert-info mb-0">
                            <div id="linkInfo"></div>
                            <input type="text" class="form-control mt-2" id="examLink" readonly>
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="copyLink()">
                                <i class="bi bi-clipboard me-1"></i>复制链接
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 详细记录 -->
            <div class="card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0"><i class="bi bi-list-ul me-2"></i>考试记录</h5>
                        <button id="refreshBtn" class="btn btn-outline-primary btn-sm"><i class="bi bi-arrow-clockwise me-1"></i>刷新</button>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>学号</th>
                                    <th>姓名</th>
                                    <th>专业</th>
                                    <th>成绩</th>
                                    <th>用时</th>
                                    <th>考试时间</th>
                                </tr>
                            </thead>
                            <tbody id="recordsBody">
                                <tr><td colspan="6" class="text-center text-muted">暂无记录</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="text-center mt-3">
                <button id="logoutBtn" class="btn btn-outline-secondary"><i class="bi bi-box-arrow-right me-2"></i>退出登录</button>
            </div>
        </div>
    </div>

    <script>
        let teacherInfo = null;
        
        function show(id){document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));document.getElementById(id).classList.add('active')}
        
        async function loadStats(){
            try{
                const res=await fetch('/api/exam/teacher/stats');
                const data=await res.json();
                if(data.success){
                    document.getElementById('totalStudents').textContent=data.stats.total_students;
                    document.getElementById('examinedCount').textContent=data.stats.examined_count;
                    document.getElementById('avgScore').textContent=data.stats.avg_score.toFixed(1);
                    document.getElementById('passRate').textContent=data.stats.pass_rate.toFixed(1)+'%';
                    
                    const tbody=document.getElementById('recordsBody');
                    if(data.records.length===0){
                        tbody.innerHTML='<tr><td colspan="6" class="text-center text-muted">暂无考试记录</td></tr>';
                    }else{
                        tbody.innerHTML=data.records.map(r=>{
                            const scoreClass=r.score>=80?'score-high':r.score>=60?'score-mid':'score-low';
                            return `<tr>
                                <td>${r.student_id}</td>
                                <td>${r.student_name}</td>
                                <td>${r.major}</td>
                                <td class="${scoreClass}">${r.score}分</td>
                                <td>${Math.floor(r.duration_seconds/60)}分${r.duration_seconds%60}秒</td>
                                <td>${r.end_time}</td>
                            </tr>`;
                        }).join('');
                    }
                }else{
                    alert(data.message);
                }
            }catch(e){
                alert('加载失败：'+e.message);
            }
            
            // 加载章节列表
            loadChapters();
        }
        
        // 加载章节列表
        async function loadChapters(){
            try{
                console.log('开始加载章节列表...');
                const res=await fetch('/api/exam/chapters');
                const data=await res.json();
                
                console.log('章节API返回:', data);
                
                if(data.success && data.chapters){
                    const select=document.getElementById('chapterSelect');
                    console.log('找到章节数量:', data.chapters.length);
                    
                    data.chapters.forEach(ch => {
                        const option=document.createElement('option');
                        option.value=ch.chapter;
                        option.textContent=ch.chapter + ' (' + ch.count + '题)';
                        select.appendChild(option);
                    });
                    
                    console.log('章节列表加载完成');
                } else {
                    console.error('章节API返回失败:', data.message);
                }
            }catch(e){
                console.error('加载章节失败', e);
                alert('加载章节失败：' + e.message);
            }
        }
        
        // 生成章节考试链接
        async function generateChapterLink(){
            const chapter=document.getElementById('chapterSelect').value;
            const mode=document.querySelector('input[name="examMode"]:checked').value;
            
            try{
                let url='/api/exam/chapter-link?mode=' + mode;
                if(chapter){
                    url += '&chapter=' + encodeURIComponent(chapter);
                }
                
                const res=await fetch(url);
                const data=await res.json();
                
                if(data.success){
                    document.getElementById('examLink').value=data.link;
                    
                    // 显示链接信息
                    let infoHtml = '<strong>考试链接已生成</strong><br>';
                    infoHtml += '<span class="badge bg-' + (data.mode === 'unified' ? 'success' : 'primary') + '">' + (data.mode === 'unified' ? '统一试卷' : '随机试卷') + '</span> ';
                    infoHtml += '<span class="badge bg-secondary">' + data.chapter + '</span>';
                    if(data.question_count){
                        infoHtml += ' <span class="text-muted small">共' + data.question_count + '题</span>';
                    }
                    document.getElementById('linkInfo').innerHTML=infoHtml;
                    
                    document.getElementById('linkDisplay').style.display='block';
                }else{
                    alert('生成链接失败：' + data.message);
                }
            }catch(e){
                alert('生成链接失败：' + e.message);
            }
        }
        
        // 复制链接
        function copyLink(){
            const linkInput=document.getElementById('examLink');
            linkInput.select();
            document.execCommand('copy');
            alert('链接已复制到剪贴板！');
        }
        
        document.getElementById('loginForm').addEventListener('submit',async function(e){
            e.preventDefault();
            const id=document.getElementById('teacherId').value.trim();
            if(!id)return alert('请输入教师工号');
            
            try{
                const res=await fetch('/api/exam/teacher/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({teacher_id:id})});
                const data=await res.json();
                if(data.success){
                    teacherInfo=data.teacher;
                    show('statsSec');
                    loadStats();
                }else{
                    alert(data.message);
                }
            }catch(e){
                alert('登录失败：'+e.message);
            }
        });
        
        document.getElementById('refreshBtn').addEventListener('click',loadStats);
        document.getElementById('logoutBtn').addEventListener('click',function(){if(confirm('确定退出？'))location.reload()});
    </script>
</body>
</html>
'''


async def teacher_login(request: Request) -> JSONResponse:
    """教师登录"""
    try:
        data = await request.json()
        teacher_id = str(data.get('teacher_id', '')).strip()
        
        if not teacher_id:
            return JSONResponse({'success': False, 'message': '请输入教师工号'})
        
        students = load_students()
        
        if teacher_id in students and students[teacher_id].get('is_teacher'):
            return JSONResponse({
                'success': True,
                'message': '登录成功',
                'teacher': students[teacher_id]
            })
        else:
            return JSONResponse({'success': False, 'message': '教师工号不存在'})
            
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'登录失败：{str(e)}'})


async def get_teacher_stats(request: Request) -> JSONResponse:
    """获取统计数据"""
    try:
        students = load_students()
        records = load_exam_records()
        
        # 统计学生数量（排除测试和教师账号）
        total_students = len([s for s in students.values() if not s.get('is_teacher') and s.get('id') != '123456'])
        
        # 统计已考试学生
        examined_ids = set(r['student_id'] for r in records if r['student_id'] != '123456')
        examined_count = len(examined_ids)
        
        # 计算平均分和及格率
        if records:
            scores = [r['score'] for r in records if r['student_id'] != '123456']
            avg_score = sum(scores) / len(scores) if scores else 0
            passed = len([s for s in scores if s >= 60])
            pass_rate = (passed / len(scores) * 100) if scores else 0
        else:
            avg_score = 0
            pass_rate = 0
        
        # 按时间倒序排列记录
        sorted_records = sorted(records, key=lambda x: x.get('end_time', ''), reverse=True)
        
        return JSONResponse({
            'success': True,
            'stats': {
                'total_students': total_students,
                'examined_count': examined_count,
                'avg_score': avg_score,
                'pass_rate': pass_rate
            },
            'records': sorted_records
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'获取统计失败：{str(e)}'})


async def get_chapters(request: Request) -> JSONResponse:
    """获取章节列表"""
    try:
        # 从题库中统计章节
        questions_dict = load_questions()
        
        # 统计每个章节的题目数量
        chapter_count = {}
        
        # 遍历所有题型的所有题目
        for q_type, questions_list in questions_dict.items():
            for q in questions_list:
                chapter = q.get('chapter', '未分类')
                chapter_count[chapter] = chapter_count.get(chapter, 0) + 1
        
        # 转换为列表并排序
        chapters = [{'chapter': k, 'count': v} for k, v in chapter_count.items()]
        
        # 按章节号排序（提取数字）
        def extract_chapter_num(chapter_obj):
            import re
            chapter_name = chapter_obj['chapter']
            # 提取章节号中的数字
            match = re.search(r'第([一二三四五六七八九十百]+)章', chapter_name)
            if match:
                chinese_num = match.group(1)
                # 中文数字转阿拉伯数字
                chinese_to_arabic = {
                    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
                    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
                }
                return chinese_to_arabic.get(chinese_num, 999)
            return 999
        
        chapters.sort(key=extract_chapter_num)
        
        print(f"章节统计完成: 共{len(chapters)}个章节")
        print(f"章节列表: {chapters}")
        
        return JSONResponse({
            'success': True,
            'chapters': chapters
        })
        
    except Exception as e:
        print(f"获取章节失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'获取章节失败：{str(e)}'})


async def refresh_cache(request: Request) -> JSONResponse:
    """刷新缓存 - 教师更换题库或学生名单后调用
    
    使用方法：
    POST /api/refresh_cache
    或
    GET /api/refresh_cache
    """
    global _questions_cache, _students_cache
    
    try:
        # 清除缓存
        old_questions_count = sum(len(v) for v in (_questions_cache or {}).values())
        old_students_count = len(_students_cache or {})
        
        _questions_cache = None
        _students_cache = None
        
        # 重新加载
        new_questions = load_questions(use_cache=False)
        new_students = load_students(use_cache=False)
        
        new_questions_count = sum(len(v) for v in new_questions.values())
        new_students_count = len(new_students)
        
        return JSONResponse({
            'success': True,
            'message': '缓存刷新成功',
            'data': {
                'questions': {
                    'before': old_questions_count,
                    'after': new_questions_count
                },
                'students': {
                    'before': old_students_count,
                    'after': new_students_count
                }
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'刷新缓存失败：{str(e)}'})


async def get_chapter_link(request: Request) -> JSONResponse:
    """生成章节考试链接
    
    参数：
    - chapter: 章节名称（可选，不传则全题库）
    - mode: 考试模式（可选，unified=统一试卷，random=随机试卷，默认random）
    
    返回：
    - link: 考试链接
    - chapter: 章节名称
    - mode: 考试模式
    - linkId: 链接ID
    - question_count: 题目数量（统一试卷模式）
    """
    try:
        # 获取参数
        chapter = request.query_params.get('chapter', '')
        mode = request.query_params.get('mode', 'random')  # 默认随机试卷
        
        # 生成链接ID
        link_id = str(__import__('random').randrange(10000000, 99999999))
        
        # 如果是统一试卷模式，预生成试卷
        if mode == 'unified':
            all_questions = load_questions()
            
            # 如果有章节参数，筛选题目
            if chapter:
                all_questions = filter_questions_by_chapter(all_questions, chapter)
            
            # 检查题目数量
            total_questions = len(all_questions['单选题']) + len(all_questions['多选题']) + len(all_questions['简答题'])
            if total_questions < 10:
                return JSONResponse({
                    'success': False, 
                    'message': f'题目数量不足（仅{total_questions}题），无法生成试卷'
                })
            
            # 预生成试卷
            selected_questions = random_select_questions(all_questions, 10)
            
            # 存储预生成试卷
            exam_papers[link_id] = {
                'questions': selected_questions,
                'chapter': chapter if chapter else '全题库',
                'mode': 'unified',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"[统一试卷] 预生成试卷 linkId={link_id}, 章节={chapter or '全题库'}, 题目数={len(selected_questions)}")
        
        # 使用Coze平台地址（从环境变量或配置中获取）
        base_url = os.getenv('COZE_BASE_URL', 'https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site')
        
        # 构建链接
        params = []
        if chapter:
            params.append(f"chapter={__import__('urllib').parse.quote(chapter)}")
        params.append(f"linkId={link_id}")
        params.append(f"mode={mode}")
        
        exam_link = f"{base_url}/exam?{'&'.join(params)}"
        
        print(f"生成考试链接: {exam_link} (模式: {mode})")
        
        response_data = {
            'success': True,
            'link': exam_link,
            'chapter': chapter if chapter else '全题库',
            'mode': mode,
            'linkId': link_id
        }
        
        # 统一试卷模式返回题目数量
        if mode == 'unified' and link_id in exam_papers:
            response_data['question_count'] = len(exam_papers[link_id]['questions'])
        
        return JSONResponse(response_data)
        
    except Exception as e:
        print(f"生成链接失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'生成链接失败：{str(e)}'})


def get_teacher_page() -> HTMLResponse:
    """返回教师管理页面"""
    return HTMLResponse(content=TEACHER_HTML)
def get_teacher_page() -> HTMLResponse:
    """返回教师管理页面"""
    return HTMLResponse(content=TEACHER_HTML)


# ============== 统一入口首页 ==============

HOME_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>火电机组考核系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary: #1a73e8;
            --success: #34a853;
            --bg: #f8f9fa;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        
        .container-box {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 60px 50px;
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        .logo {
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, var(--primary) 0%, #1557b0 100%);
            border-radius: 50%;
            margin: 0 auto 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 30px rgba(26, 115, 232, 0.3);
        }
        
        .logo i {
            font-size: 50px;
            color: white;
        }
        
        h1 {
            color: #333;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 16px;
            margin-bottom: 40px;
        }
        
        .entry-cards {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-top: 30px;
        }
        
        .entry-card {
            display: block;
            padding: 30px;
            border-radius: 15px;
            text-decoration: none;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .entry-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
        }
        
        .entry-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        }
        
        .student-card {
            background: linear-gradient(135deg, var(--primary) 0%, #1557b0 100%);
            color: white;
        }
        
        .teacher-card {
            background: linear-gradient(135deg, var(--success) 0%, #2d8a47 100%);
            color: white;
        }
        
        .card-icon {
            font-size: 40px;
            margin-bottom: 15px;
        }
        
        .card-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .card-desc {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .card-arrow {
            position: absolute;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 24px;
            opacity: 0;
            transition: all 0.3s ease;
        }
        
        .entry-card:hover .card-arrow {
            opacity: 1;
            right: 20px;
        }
        
        .info-box {
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid var(--primary);
        }
        
        .info-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            color: #666;
            font-size: 14px;
        }
        
        .info-item:last-child {
            margin-bottom: 0;
        }
        
        .info-item i {
            margin-right: 10px;
            color: var(--primary);
        }
        
        @media (max-width: 576px) {
            .container-box {
                padding: 40px 30px;
            }
            
            h1 {
                font-size: 26px;
            }
            
            .entry-card {
                padding: 25px;
            }
            
            .card-title {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container-box">
        <div class="logo">
            <i class="bi bi-lightning-charge-fill"></i>
        </div>
        
        <h1>火电机组考核系统</h1>
        <p class="subtitle">基于《火电厂热工自动控制技术及应用》教材</p>
        
        <div class="entry-cards">
            <a href="exam" class="entry-card student-card">
                <div class="card-icon">
                    <i class="bi bi-mortarboard-fill"></i>
                </div>
                <div class="card-title">学生考试入口</div>
                <div class="card-desc">学号验证 → 随机抽题 → 在线答题 → 自动判分</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
            
            <a href="teacher" class="entry-card teacher-card">
                <div class="card-icon">
                    <i class="bi bi-person-badge-fill"></i>
                </div>
                <div class="card-title">教师管理入口</div>
                <div class="card-desc">查看统计 · 考试记录 · 数据分析 · 成绩管理</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
        </div>
        
        <div class="info-box">
            <div class="info-item">
                <i class="bi bi-people-fill"></i>
                <span>题库：244题 · 学生：70人</span>
            </div>
            <div class="info-item">
                <i class="bi bi-book-fill"></i>
                <span>题型：单选 + 多选 + 简答（共10题）</span>
            </div>
        </div>
    </div>
</body>
</html>
'''

def get_home_page() -> HTMLResponse:
    """返回统一入口首页"""
    return HTMLResponse(content=HOME_HTML)
