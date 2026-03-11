"""火电机组考核系统 - FastAPI路由"""
import os
import json
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from coze_coding_dev_sdk import LLMClient, SearchClient, DocumentGenerationClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage

# 配置 - 使用绝对路径
WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
STUDENT_FILE = os.path.join(WORKSPACE_PATH, 'assets', '火电机组考核学生名单.xlsx')
QUESTION_FILE = os.path.join(WORKSPACE_PATH, 'assets', '《火电厂热工自动控制技术及应用》_100题.xlsx')

# 会话存储
exam_sessions: Dict[str, Dict] = {}


def load_students() -> Dict[str, Dict]:
    """加载学生名单"""
    df = pd.read_excel(STUDENT_FILE)
    students = {}
    for _, row in df.iterrows():
        student_id = str(row['学号']).strip()
        students[student_id] = {
            'id': student_id,
            'name': str(row['姓名']).strip(),
            'major': str(row.get('专业', row.get('班级', ''))).strip()
        }
    return students


def load_questions() -> Dict[str, List]:
    """加载题库"""
    questions = {'单选题': [], '多选题': [], '简答题': []}
    
    # 加载单选题
    df_single = pd.read_excel(QUESTION_FILE, sheet_name='单选题')
    for _, row in df_single.iterrows():
        questions['单选题'].append({
            'type': '单选题',
            'id': int(row['题号']),
            'chapter': str(row['章节']),
            'chapter_title': str(row['章节名称']),
            'page': str(row['页码']),
            'question': str(row['题目内容']),
            'options': {
                'A': str(row['选项A']),
                'B': str(row['选项B']),
                'C': str(row['选项C']),
                'D': str(row['选项D'])
            },
            'answer': str(row['答案']),
            'analysis': str(row['解析']),
            'difficulty': str(row['难度'])
        })
    
    # 加载多选题
    df_multiple = pd.read_excel(QUESTION_FILE, sheet_name='多选题')
    for _, row in df_multiple.iterrows():
        answer = str(row['答案'])
        if ',' in answer:
            answer_list = [a.strip() for a in answer.split(',')]
        else:
            answer_list = [a.strip() for a in answer.replace('，', ',').split(',') if a.strip()]
        
        questions['多选题'].append({
            'type': '多选题',
            'id': int(row['题号']),
            'chapter': str(row['章节']),
            'chapter_title': str(row['章节名称']),
            'page': str(row['页码']),
            'question': str(row['题目内容']),
            'options': {
                'A': str(row['选项A']),
                'B': str(row['选项B']),
                'C': str(row['选项C']),
                'D': str(row['选项D'])
            },
            'answer': answer_list,
            'analysis': str(row['解析']),
            'difficulty': str(row['难度'])
        })
    
    # 加载简答题
    df_short = pd.read_excel(QUESTION_FILE, sheet_name='简答题')
    for _, row in df_short.iterrows():
        questions['简答题'].append({
            'type': '简答题',
            'id': int(row['题号']),
            'chapter': str(row['章节']),
            'chapter_title': str(row['章节名称']),
            'page': str(row['页码']),
            'question': str(row['题目内容']),
            'answer': str(row['答案']),
            'analysis': str(row['解析']),
            'difficulty': str(row['难度'])
        })
    
    return questions


def generate_session_id(student_id: str) -> str:
    """生成会话ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{student_id}_{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def random_select_questions(all_questions: Dict, count: int = 10) -> List:
    """随机抽取题目"""
    selected = []
    
    single_count = 4
    multiple_count = 3
    short_count = 3
    
    single_questions = random.sample(all_questions['单选题'], min(single_count, len(all_questions['单选题'])))
    multiple_questions = random.sample(all_questions['多选题'], min(multiple_count, len(all_questions['多选题'])))
    short_questions = random.sample(all_questions['简答题'], min(short_count, len(all_questions['简答题'])))
    
    for i, q in enumerate(single_questions, 1):
        q['seq'] = i
        selected.append(q)
    
    for i, q in enumerate(multiple_questions, len(single_questions) + 1):
        q['seq'] = i
        selected.append(q)
    
    for i, q in enumerate(short_questions, len(single_questions) + len(multiple_questions) + 1):
        q['seq'] = i
        selected.append(q)
    
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
            if user_answer == correct_answer:
                is_correct = True
                score = 10
        elif q_type == '多选题':
            if isinstance(user_answer, list):
                user_set = set(user_answer)
            else:
                user_set = set(user_answer.split(',')) if user_answer else set()
            
            correct_set = set(correct_answer) if isinstance(correct_answer, list) else set(correct_answer.split(','))
            
            if user_set == correct_set:
                is_correct = True
                score = 10
        elif q_type == '简答题':
            user_answer_text = str(user_answer).lower()
            correct_answer_text = str(correct_answer).lower()
            
            keywords = correct_answer_text.replace('，', ' ').replace('。', ' ').replace('、', ' ').split()
            matched = sum(1 for kw in keywords if len(kw) > 2 and kw in user_answer_text)
            match_ratio = matched / max(len([kw for kw in keywords if len(kw) > 2]), 1)
            
            if match_ratio >= 0.6:
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
            'chapter_title': q['chapter_title'],
            'page': q['page'],
            'difficulty': q['difficulty']
        })
    
    return total_score, results


def get_extension_content(question_text: str, chapter_title: str) -> str:
    """获取前沿拓展内容"""
    try:
        ctx = new_context(method="get_extension")
        search_client = SearchClient(ctx=ctx)
        
        search_query = f"火电厂热工自动控制 {chapter_title} 最新技术 行业案例 科研进展"
        
        response = search_client.web_search(
            query=search_query,
            count=3,
            need_summary=True
        )
        
        extension_content = "## 前沿拓展\n\n"
        
        if response.web_items:
            extension_content += "### 相关最新资讯\n\n"
            for i, item in enumerate(response.web_items[:3], 1):
                extension_content += f"**{i}. {item.title}**\n\n"
                extension_content += f"来源：{item.site_name}\n\n"
                if item.snippet:
                    extension_content += f"{item.snippet}\n\n"
                extension_content += f"[查看详情]({item.url})\n\n"
        
        if response.summary:
            extension_content += f"### AI总结\n\n{response.summary}\n\n"
        
        return extension_content
        
    except Exception as e:
        return f"## 前沿拓展\n\n暂无相关拓展信息。"


def generate_report(student_info: Dict, questions: List, results: List, total_score: int, extensions: Dict) -> str:
    """生成学习报告"""
    report = f"""# 火电机组考核学习报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | {student_info['name']} |
| 学号 | {student_info['id']} |
| 专业 | {student_info['major']} |
| 考核时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 总分 | **{total_score}** / 100 分 |

## 成绩分析

### 题型得分

| 题型 | 题数 | 正确 | 得分 |
|------|------|------|------|
| 单选题 | 4 | {sum(1 for r in results if r['type'] == '单选题' and r['is_correct'])} | {sum(r['score'] for r in results if r['type'] == '单选题')} |
| 多选题 | 3 | {sum(1 for r in results if r['type'] == '多选题' and r['is_correct'])} | {sum(r['score'] for r in results if r['type'] == '多选题')} |
| 简答题 | 3 | {sum(1 for r in results if r['type'] == '简答题' and r['is_correct'])} | {sum(r['score'] for r in results if r['type'] == '简答题')} |

---

## 答题详情

"""
    
    for i, result in enumerate(results, 1):
        correct_mark = "正确" if result['is_correct'] else "错误"
        
        report += f"### 题目 {i}：{result['type']}（{result['difficulty']}）\n\n"
        report += f"**章节**：{result['chapter']} {result['chapter_title']}（第{result['page']}页）\n\n"
        report += f"**题目**：{result['question']}\n\n"
        
        if result['options']:
            report += "**选项**：\n\n"
            for opt, content in result['options'].items():
                marker = "→ " if opt == result['user_answer'] or (isinstance(result['user_answer'], list) and opt in result['user_answer']) else "  "
                correct_marker = " (正确答案)" if opt == result['correct_answer'] or (isinstance(result['correct_answer'], list) and opt in result['correct_answer']) else ""
                report += f"{marker}**{opt}**. {content}{correct_marker}\n\n"
        
        report += f"**你的答案**：{result['user_answer'] if result['user_answer'] else '未作答'}\n\n"
        report += f"**正确答案**：{result['correct_answer']}\n\n"
        report += f"**得分**：{result['score']} / 10 分 ({correct_mark})\n\n"
        report += f"**解析**：\n\n{result['analysis']}\n\n"
        
        if str(i) in extensions:
            report += f"\n{extensions[str(i)]}\n\n"
        
        report += "---\n\n"
    
    report += f"""
---

## 学习建议

根据本次考核表现，建议重点复习以下内容：

"""
    
    wrong_questions = [r for r in results if not r['is_correct']]
    if wrong_questions:
        for r in wrong_questions:
            report += f"- {r['chapter']} {r['chapter_title']}：{r['question'][:50]}...\n"
    else:
        report += "- 恭喜！全部答对，继续保持！\n"
    
    report += "\n---\n\n*本报告由火电机组考核系统自动生成*\n"
    
    return report


# HTML模板
EXAM_HTML = '''
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
            --primary-color: #2563eb;
            --success-color: #10b981;
            --danger-color: #ef4444;
            --warning-color: #f59e0b;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 0;
            margin: 0;
        }
        .app-container { max-width: 900px; margin: 0 auto; padding: 20px; min-height: 100vh; }
        .card { border: none; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px 16px 0 0 !important;
            padding: 20px;
            border: none;
        }
        .card-header h1, .card-header h4 { margin: 0; font-weight: 600; }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 12px 30px;
            font-weight: 500;
            border-radius: 8px;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .form-control { border-radius: 8px; padding: 12px 16px; border: 2px solid #e5e7eb; }
        .form-control:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .question-card {
            background: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        .question-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .question-type { font-size: 12px; padding: 4px 12px; border-radius: 20px; font-weight: 500; }
        .type-single { background: #dbeafe; color: #1e40af; }
        .type-multiple { background: #fef3c7; color: #92400e; }
        .type-short { background: #d1fae5; color: #065f46; }
        .difficulty-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
        .diff-easy { background: #d1fae5; color: #065f46; }
        .diff-medium { background: #fef3c7; color: #92400e; }
        .diff-hard { background: #fee2e2; color: #991b1b; }
        .option-item {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-item:hover { border-color: #667eea; background: #f0f4ff; }
        .option-item.selected { border-color: #667eea; background: #dbeafe; }
        .option-item.correct { border-color: #10b981; background: #d1fae5; }
        .option-item.wrong { border-color: #ef4444; background: #fee2e2; }
        .analysis-box {
            background: #f0f9ff;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            border: 1px solid #bae6fd;
        }
        .extension-box {
            background: #fefce8;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            border: 1px solid #fef08a;
        }
        .result-card { text-align: center; padding: 30px; }
        .score-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: white;
            font-size: 48px;
            font-weight: bold;
        }
        .progress-bar-custom { height: 8px; border-radius: 4px; background: #e5e7eb; margin: 10px 0; }
        .progress-bar-custom .progress-fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
        }
        .timer { font-size: 24px; font-weight: 600; color: #667eea; }
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 768px) {
            .app-container { padding: 10px; }
            .card-header { padding: 15px; }
            .card-header h1 { font-size: 1.5rem; }
            .question-card { padding: 15px; }
            .score-circle { width: 120px; height: 120px; font-size: 36px; }
            .btn-primary { width: 100%; padding: 14px; }
        }
        .section { display: none; }
        .section.active { display: block; }
        .short-answer-input { min-height: 120px; resize: vertical; }
        .result-mark { font-size: 24px; margin-left: 10px; }
        .text-success { color: #10b981; }
        .text-danger { color: #ef4444; }
        .text-warning { color: #f59e0b; }
    </style>
</head>
<body>
    <div class="app-container">
        <div id="loginSection" class="section active">
            <div class="card">
                <div class="card-header text-center">
                    <h1><i class="bi bi-lightning-charge-fill"></i> 火电机组考核系统</h1>
                    <p class="mb-0 mt-2">《火电厂热工自动控制技术及应用》</p>
                </div>
                <div class="card-body p-4">
                    <div class="text-center mb-4">
                        <i class="bi bi-person-circle" style="font-size: 80px; color: #667eea;"></i>
                    </div>
                    <form id="loginForm">
                        <div class="mb-4">
                            <label class="form-label fw-bold">请输入学号</label>
                            <input type="text" class="form-control form-control-lg" id="studentId" placeholder="请输入您的学号" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 btn-lg">
                            <i class="bi bi-box-arrow-in-right me-2"></i>登录验证
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <div id="readySection" class="section">
            <div class="card">
                <div class="card-header"><h4><i class="bi bi-person-check me-2"></i>验证成功</h4></div>
                <div class="card-body p-4">
                    <div class="text-center mb-4">
                        <div class="alert alert-success">
                            <h5 class="mb-2">欢迎，<span id="studentName"></span> 同学！</h5>
                            <p class="mb-0">学号：<span id="studentIdDisplay"></span></p>
                            <p class="mb-0">专业：<span id="studentMajor"></span></p>
                        </div>
                    </div>
                    <div class="alert alert-info">
                        <h6 class="alert-heading"><i class="bi bi-info-circle me-2"></i>考试说明</h6>
                        <ul class="mb-0">
                            <li>本次考试共 <strong>10</strong> 道题（4道单选 + 3道多选 + 3道简答）</li>
                            <li>每题 10 分，满分 100 分</li>
                            <li>提交后可查看答案解析和前沿拓展</li>
                            <li>支持导出完整学习报告</li>
                        </ul>
                    </div>
                    <button id="startExamBtn" class="btn btn-primary btn-lg w-100">
                        <i class="bi bi-play-circle me-2"></i>开始答题
                    </button>
                </div>
            </div>
        </div>
        
        <div id="examSection" class="section">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h4 class="mb-0"><i class="bi bi-file-text me-2"></i>答题中</h4>
                    <span class="timer" id="timer">00:00</span>
                </div>
                <div class="card-body p-3 p-md-4">
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-2">
                            <span>答题进度</span>
                            <span id="progressText">0 / 10</span>
                        </div>
                        <div class="progress-bar-custom">
                            <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                        </div>
                    </div>
                    <div id="questionsContainer"></div>
                    <div class="text-center mt-4">
                        <button id="submitExamBtn" class="btn btn-primary btn-lg px-5">
                            <i class="bi bi-check-circle me-2"></i>提交答卷
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="resultSection" class="section">
            <div class="card">
                <div class="card-header text-center"><h4><i class="bi bi-trophy me-2"></i>考核完成</h4></div>
                <div class="card-body p-4">
                    <div class="result-card">
                        <div class="score-circle" id="scoreDisplay">0</div>
                        <h4 class="mt-3">总分：<span id="totalScoreText">0</span> / 100 分</h4>
                        <p id="scoreComment" class="text-muted"></p>
                    </div>
                    <div class="row text-center mb-4">
                        <div class="col-4"><div class="card p-3"><h3 class="text-primary" id="correctCount">0</h3><small>正确</small></div></div>
                        <div class="col-4"><div class="card p-3"><h3 class="text-danger" id="wrongCount">0</h3><small>错误</small></div></div>
                        <div class="col-4"><div class="card p-3"><h3 class="text-warning" id="partialCount">0</h3><small>部分得分</small></div></div>
                    </div>
                    <div id="resultsContainer"></div>
                    <div class="text-center mt-4">
                        <button id="exportReportBtn" class="btn btn-success btn-lg me-2">
                            <i class="bi bi-download me-2"></i>导出学习报告
                        </button>
                        <button id="restartBtn" class="btn btn-outline-secondary btn-lg">
                            <i class="bi bi-arrow-repeat me-2"></i>重新开始
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let sessionId = null;
        let questions = [];
        let answers = {};
        let extensions = {};
        let timer = null;
        let seconds = 0;
        const API_BASE = '';
        
        function showSection(sectionId) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
        }
        
        function updateTimer() {
            seconds++;
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            document.getElementById('timer').textContent = `${mins}:${secs}`;
        }
        
        function updateProgress() {
            const answered = Object.keys(answers).length;
            const total = questions.length;
            const percent = (answered / total) * 100;
            document.getElementById('progressText').textContent = `${answered} / ${total}`;
            document.getElementById('progressBar').style.width = `${percent}%`;
        }
        
        function renderQuestions() {
            const container = document.getElementById('questionsContainer');
            container.innerHTML = '';
            
            questions.forEach((q, index) => {
                const qCard = document.createElement('div');
                qCard.className = 'question-card fade-in';
                qCard.id = `question-${q.seq}`;
                
                let typeClass = 'type-single';
                let typeLabel = '单选题';
                if (q.type === '多选题') { typeClass = 'type-multiple'; typeLabel = '多选题'; }
                else if (q.type === '简答题') { typeClass = 'type-short'; typeLabel = '简答题'; }
                
                let diffClass = 'diff-medium';
                if (q.difficulty === '基础') diffClass = 'diff-easy';
                else if (q.difficulty === '困难') diffClass = 'diff-hard';
                
                let optionsHtml = '';
                if (q.type === '单选题' || q.type === '多选题') {
                    optionsHtml = '<div class="options-container">';
                    Object.entries(q.options).forEach(([key, value]) => {
                        const inputType = q.type === '单选题' ? 'radio' : 'checkbox';
                        optionsHtml += `
                            <div class="option-item" data-seq="${q.seq}" data-option="${key}">
                                <label class="d-flex align-items-start">
                                    <input type="${inputType}" name="q${q.seq}" value="${key}" class="me-2 mt-1" style="min-width: 18px;">
                                    <span><strong>${key}.</strong> ${value}</span>
                                </label>
                            </div>`;
                    });
                    optionsHtml += '</div>';
                } else {
                    optionsHtml = `<textarea class="form-control short-answer-input mt-3" data-seq="${q.seq}" placeholder="请在此输入您的答案..."></textarea>`;
                }
                
                qCard.innerHTML = `
                    <div class="question-header">
                        <span class="question-type ${typeClass}">${typeLabel}</span>
                        <span class="difficulty-badge ${diffClass}">${q.difficulty}</span>
                    </div>
                    <p class="mb-2"><small class="text-muted">${q.chapter} ${q.chapter_title}</small></p>
                    <h6 class="mb-3">${q.seq}. ${q.question}</h6>
                    ${optionsHtml}`;
                
                container.appendChild(qCard);
            });
            
            bindOptionEvents();
        }
        
        function bindOptionEvents() {
            document.querySelectorAll('.option-item').forEach(item => {
                item.addEventListener('click', function() {
                    const seq = this.dataset.seq;
                    const option = this.dataset.option;
                    const input = this.querySelector('input');
                    const qType = questions.find(q => q.seq == seq).type;
                    
                    if (qType === '单选题') {
                        document.querySelectorAll(`[data-seq="${seq}"]`).forEach(opt => opt.classList.remove('selected'));
                        this.classList.add('selected');
                        input.checked = true;
                        answers[seq] = option;
                    } else {
                        this.classList.toggle('selected');
                        input.checked = !input.checked;
                        const selected = [];
                        document.querySelectorAll(`[data-seq="${seq}"].selected`).forEach(opt => selected.push(opt.dataset.option));
                        answers[seq] = selected;
                    }
                    updateProgress();
                });
            });
            
            document.querySelectorAll('.short-answer-input').forEach(textarea => {
                textarea.addEventListener('input', function() {
                    answers[this.dataset.seq] = this.value.trim();
                    updateProgress();
                });
            });
        }
        
        function renderResults(results) {
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '';
            
            results.forEach((r, index) => {
                const rCard = document.createElement('div');
                rCard.className = 'question-card fade-in';
                
                let resultIcon = r.is_correct ? '✅' : (r.score > 0 ? '⚠️' : '❌');
                let resultClass = r.is_correct ? 'text-success' : (r.score > 0 ? 'text-warning' : 'text-danger');
                
                let optionsHtml = '';
                if (r.options) {
                    optionsHtml = '<div class="options-container">';
                    Object.entries(r.options).forEach(([key, value]) => {
                        let optClass = '';
                        const userAns = r.user_answer;
                        const correctAns = r.correct_answer;
                        const isSelected = (Array.isArray(userAns) && userAns.includes(key)) || userAns === key;
                        const isCorrect = (Array.isArray(correctAns) && correctAns.includes(key)) || correctAns === key;
                        
                        if (isCorrect) optClass = 'correct';
                        else if (isSelected && !isCorrect) optClass = 'wrong';
                        
                        const icon = isCorrect ? '✓' : (isSelected && !isCorrect ? '✗' : '');
                        optionsHtml += `<div class="option-item ${optClass}"><span><strong>${key}.</strong> ${value} ${icon}</span></div>`;
                    });
                    optionsHtml += '</div>';
                }
                
                rCard.innerHTML = `
                    <div class="question-header">
                        <span>
                            <span class="question-type type-${r.type === '单选题' ? 'single' : r.type === '多选题' ? 'multiple' : 'short'}">${r.type}</span>
                            <span class="result-mark ${resultClass}">${resultIcon}</span>
                        </span>
                        <span class="fw-bold">${r.score} / 10 分</span>
                    </div>
                    <p class="mb-2"><small class="text-muted">${r.chapter} ${r.chapter_title}（第${r.page}页）</small></p>
                    <h6 class="mb-3">${r.seq}. ${r.question}</h6>
                    ${optionsHtml}
                    ${r.type === '简答题' ? `
                        <div class="mt-3">
                            <p><strong>你的答案：</strong></p>
                            <div class="alert ${r.score >= 10 ? 'alert-success' : r.score >= 5 ? 'alert-warning' : 'alert-danger'}">${r.user_answer || '未作答'}</div>
                            <p><strong>参考答案：</strong></p>
                            <div class="alert alert-info">${r.correct_answer}</div>
                        </div>` : `
                        <p class="mt-2"><strong>你的答案：</strong>${Array.isArray(r.user_answer) ? r.user_answer.join(', ') : r.user_answer || '未作答'} &nbsp;&nbsp; <strong>正确答案：</strong>${Array.isArray(r.correct_answer) ? r.correct_answer.join(', ') : r.correct_answer}</p>`}
                    <div class="analysis-box"><h6><i class="bi bi-lightbulb me-2"></i>解析</h6><p class="mb-0">${r.analysis}</p></div>
                    <div class="extension-box" id="extension-${r.seq}">
                        <h6><i class="bi bi-search me-2"></i>前沿拓展</h6>
                        <button class="btn btn-sm btn-outline-primary" onclick="loadExtension(${r.seq}, '${r.chapter_title}')"><i class="bi bi-arrow-clockwise me-1"></i>点击加载</button>
                    </div>`;
                
                container.appendChild(rCard);
            });
        }
        
        async function loadExtension(seq, chapterTitle) {
            const extDiv = document.getElementById(`extension-${seq}`);
            extDiv.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> 加载中...</div>';
            const q = questions.find(q => q.seq === seq);
            
            try {
                const response = await fetch(`${API_BASE}/api/exam/extension`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: q.question, chapter_title: chapterTitle})
                });
                const data = await response.json();
                
                if (data.success) {
                    extensions[seq] = data.extension;
                    extDiv.innerHTML = `<h6><i class="bi bi-search me-2"></i>前沿拓展</h6><div class="extension-content">${data.extension.replace(/\\n/g, '<br>')}</div>`;
                } else {
                    extDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (error) {
                extDiv.innerHTML = `<div class="alert alert-danger">加载失败：${error.message}</div>`;
            }
        }
        
        async function apiCall(endpoint, data) {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            return await response.json();
        }
        
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const studentId = document.getElementById('studentId').value.trim();
            if (!studentId) { alert('请输入学号'); return; }
            
            try {
                const result = await apiCall('/api/exam/verify', {student_id: studentId});
                if (result.success) {
                    sessionId = result.session_id;
                    document.getElementById('studentName').textContent = result.student.name;
                    document.getElementById('studentIdDisplay').textContent = result.student.id;
                    document.getElementById('studentMajor').textContent = result.student.major;
                    showSection('readySection');
                } else {
                    alert(result.message);
                }
            } catch (error) {
                alert('验证失败：' + error.message);
            }
        });
        
        document.getElementById('startExamBtn').addEventListener('click', async function() {
            this.disabled = true;
            this.innerHTML = '<div class="loading-spinner me-2"></div>加载题目...';
            
            try {
                const result = await apiCall('/api/exam/start', {session_id: sessionId});
                if (result.success) {
                    questions = result.questions;
                    renderQuestions();
                    showSection('examSection');
                    timer = setInterval(updateTimer, 1000);
                } else {
                    alert(result.message);
                    this.disabled = false;
                    this.innerHTML = '<i class="bi bi-play-circle me-2"></i>开始答题';
                }
            } catch (error) {
                alert('开始失败：' + error.message);
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-play-circle me-2"></i>开始答题';
            }
        });
        
        document.getElementById('submitExamBtn').addEventListener('click', async function() {
            if (Object.keys(answers).length < questions.length && !confirm('还有题目未作答，确定要提交吗？')) return;
            
            this.disabled = true;
            this.innerHTML = '<div class="loading-spinner me-2"></div>提交中...';
            
            try {
                clearInterval(timer);
                const result = await apiCall('/api/exam/submit', {session_id: sessionId, answers: answers});
                
                if (result.success) {
                    document.getElementById('scoreDisplay').textContent = result.score;
                    document.getElementById('totalScoreText').textContent = result.score;
                    
                    let correct = 0, wrong = 0, partial = 0;
                    result.results.forEach(r => {
                        if (r.is_correct) correct++;
                        else if (r.score > 0) partial++;
                        else wrong++;
                    });
                    
                    document.getElementById('correctCount').textContent = correct;
                    document.getElementById('wrongCount').textContent = wrong;
                    document.getElementById('partialCount').textContent = partial;
                    
                    let comment = result.score >= 90 ? '优秀！继续保持！' : result.score >= 80 ? '良好，再接再厉！' : result.score >= 60 ? '及格，需要加强学习。' : '不及格，请认真复习。';
                    document.getElementById('scoreComment').textContent = comment;
                    
                    renderResults(result.results);
                    showSection('resultSection');
                } else {
                    alert(result.message);
                    this.disabled = false;
                    this.innerHTML = '<i class="bi bi-check-circle me-2"></i>提交答卷';
                }
            } catch (error) {
                alert('提交失败：' + error.message);
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-check-circle me-2"></i>提交答卷';
            }
        });
        
        document.getElementById('exportReportBtn').addEventListener('click', async function() {
            this.disabled = true;
            this.innerHTML = '<div class="loading-spinner me-2"></div>生成中...';
            
            try {
                const result = await apiCall('/api/exam/export', {session_id: sessionId, extensions: extensions});
                if (result.success) {
                    window.open(result.download_url, '_blank');
                    alert('报告已生成，请在新窗口下载！');
                } else {
                    alert(result.message);
                }
            } catch (error) {
                alert('导出失败：' + error.message);
            }
            
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-download me-2"></i>导出学习报告';
        });
        
        document.getElementById('restartBtn').addEventListener('click', function() {
            if (confirm('确定要重新开始吗？')) location.reload();
        });
    </script>
</body>
</html>
'''


# API处理函数
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
            'message': f'验证成功，欢迎 {student["name"]} 同学！',
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
        
        exam_sessions[session_id]['questions'] = selected_questions
        exam_sessions[session_id]['start_time'] = datetime.now().isoformat()
        
        questions_for_client = []
        for q in selected_questions:
            q_copy = {
                'seq': q['seq'],
                'type': q['type'],
                'question': q['question'],
                'options': q.get('options'),
                'chapter': q['chapter'],
                'chapter_title': q['chapter_title'],
                'difficulty': q['difficulty']
            }
            questions_for_client.append(q_copy)
        
        return JSONResponse({
            'success': True,
            'questions': questions_for_client,
            'total': len(questions_for_client)
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
        
        exam_sessions[session_id]['answers'] = answers
        exam_sessions[session_id]['results'] = results
        exam_sessions[session_id]['total_score'] = total_score
        exam_sessions[session_id]['end_time'] = datetime.now().isoformat()
        
        return JSONResponse({
            'success': True,
            'score': total_score,
            'results': results
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'提交失败：{str(e)}'})


async def exam_extension(request: Request) -> JSONResponse:
    """获取前沿拓展"""
    try:
        data = await request.json()
        question_text = data.get('question', '')
        chapter_title = data.get('chapter_title', '')
        
        extension = get_extension_content(question_text, chapter_title)
        
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
        
        report_content = generate_report(
            session['student'],
            session['questions'],
            session['results'],
            session['total_score'],
            extensions
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
