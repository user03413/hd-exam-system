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
STUDENT_FILE = os.path.join(WORKSPACE_PATH, 'assets', '火电机组考核学生名单.xlsx')
QUESTION_FILE = os.path.join(WORKSPACE_PATH, 'assets', '244题_热工自动化试题集.xlsx')

# 会话存储
exam_sessions: Dict[str, Dict] = {}


def load_students() -> Dict[str, Dict]:
    """加载学生名单"""
    try:
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
        students['0000000000'] = {
            'id': '0000000000',
            'name': '测试学生',
            'major': '控制工程（测试）'
        }
        
        return students
    except Exception as e:
        print(f"加载学生名单失败: {e}")
        # 即使加载失败，也返回测试账号
        return {
            '0000000000': {
                'id': '0000000000',
                'name': '测试学生',
                'major': '控制工程（测试）'
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


def load_questions() -> Dict[str, List]:
    """加载题库"""
    try:
        df = pd.read_excel(QUESTION_FILE, sheet_name='244 题')
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
        
        print(f"题库加载完成: 单选{len(questions['单选题'])}题, 多选{len(questions['多选题'])}题, 简答{len(questions['简答题'])}题")
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
            <div class="sub">热工自动化在线考试</div>
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
        let sessionId = null, questions = [], answers = {}, extensions = {}, timer = null, seconds = 0;
        
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
                
                div.innerHTML = '<div class="q-header"><span><span class="q-type ' + typeCls + '">' + q.type + '</span> <span class="' + diffCls + '">' + q.difficulty + '</span></span><span class="text-muted small">第' + q.seq + '题</span></div><div class="q-chapter"><i class="bi bi-book"></i> ' + q.chapter + (q.page ? '（第' + q.page + '页）' : '') + '</div><div class="q-text">' + q.question + '</div>' + optHtml;
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
                
                div.innerHTML = '<div class="q-header"><span><span class="q-type type-' + (r.type === '单选题' ? '单选' : r.type === '多选题' ? '多选' : '简答') + '">' + r.type + '</span> <span class="' + cls + '">' + icon + '</span></span><span class="fw-bold">' + r.score + '/10分</span></div><div class="q-chapter">' + r.chapter + '</div><div class="q-text">' + r.seq + '. ' + r.question + '</div>' + optHtml + ansHtml + '<div class="analysis"><h6><i class="bi bi-lightbulb"></i> 解析</h6><p class="mb-0 small">' + r.analysis + '</p></div><div class="ext" id="ext-' + r.seq + '"><h6><i class="bi bi-search"></i> 前沿拓展</h6><button class="btn btn-sm btn-outline-warning" onclick="loadExt(' + r.seq + ')">点击加载</button></div>';
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
                const r = await api('/verify', {student_id: id});
                if (r.success) {
                    sessionId = r.session_id;
                    document.getElementById('sName').textContent = r.student.name;
                    document.getElementById('sId').textContent = r.student.id;
                    document.getElementById('sMajor').textContent = r.student.major;
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
    """验证学号"""
    try:
        data = await request.json()
        student_id = str(data.get('student_id', '')).strip()
        
        if not student_id:
            return JSONResponse({'success': False, 'message': '请输入学号'})
        
        students = load_students()
        
        if student_id not in students:
            return JSONResponse({'success': False, 'message': '学号不存在，请检查输入'})
        
        student = students[student_id]
        session_id = generate_session_id(student_id)
        
        exam_sessions[session_id] = {
            'student': student,
            'questions': None,
            'answers': {},
            'start_time': datetime.now().isoformat()
        }
        
        return JSONResponse({
            'success': True,
            'message': f"验证成功，欢迎 {student['name']} 同学！",
            'student': student,
            'session_id': session_id
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'验证失败：{str(e)}'})


async def exam_start(request: Request) -> JSONResponse:
    """开始考试"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in exam_sessions:
            return JSONResponse({'success': False, 'message': '会话无效，请重新登录'})
        
        all_questions = load_questions()
        selected_questions = random_select_questions(all_questions, 10)
        
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
        
        return JSONResponse({
            'success': True,
            'questions': questions_for_client,
            'total': len(questions_for_client),
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
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
