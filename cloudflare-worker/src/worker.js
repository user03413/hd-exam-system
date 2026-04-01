// 火电机组考核系统 - Cloudflare Workers 后端

import { Router } from 'itty-router';

const router = Router();

// CORS 头
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// 会话存储（内存中，生产环境应使用 KV）
const sessions = {};

// 统一入口首页
const HOME_HTML = `
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
        * { box-sizing: border-box; }
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
        .logo i { font-size: 50px; color: white; }
        h1 { color: #333; font-size: 32px; font-weight: 700; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 16px; margin-bottom: 40px; }
        .entry-cards { display: flex; flex-direction: column; gap: 20px; margin-top: 30px; }
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
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
        }
        .entry-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        }
        .student-card { background: linear-gradient(135deg, var(--primary) 0%, #1557b0 100%); color: white; }
        .teacher-card { background: linear-gradient(135deg, var(--success) 0%, #2d8a47 100%); color: white; }
        .card-icon { font-size: 40px; margin-bottom: 15px; }
        .card-title { font-size: 24px; font-weight: 700; margin-bottom: 10px; }
        .card-desc { font-size: 14px; opacity: 0.9; }
        .card-arrow {
            position: absolute;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 24px;
            opacity: 0;
            transition: all 0.3s ease;
        }
        .entry-card:hover .card-arrow { opacity: 1; right: 20px; }
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
        .info-item:last-child { margin-bottom: 0; }
        .info-item i { margin-right: 10px; color: var(--primary); }
        @media (max-width: 576px) {
            .container-box { padding: 40px 30px; }
            h1 { font-size: 26px; }
            .entry-card { padding: 25px; }
            .card-title { font-size: 20px; }
        }
    </style>
</head>
<body>
    <div class="container-box">
        <div class="logo"><i class="bi bi-lightning-charge-fill"></i></div>
        <h1>火电机组考核系统</h1>
        <p class="subtitle">基于《火电厂热工自动控制技术及应用》教材</p>
        <div class="entry-cards">
            <a href="exam" class="entry-card student-card">
                <div class="card-icon"><i class="bi bi-mortarboard-fill"></i></div>
                <div class="card-title">学生考试入口</div>
                <div class="card-desc">学号验证 → 随机抽题 → 在线答题 → 自动判分</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
            <a href="teacher" class="entry-card teacher-card">
                <div class="card-icon"><i class="bi bi-person-badge-fill"></i></div>
                <div class="card-title">教师管理入口</div>
                <div class="card-desc">查看统计 · 考试记录 · 数据分析 · 成绩管理</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
        </div>
        <div class="info-box">
            <div class="info-item"><i class="bi bi-people-fill"></i><span>题库：244题 · 学生：70人</span></div>
            <div class="info-item"><i class="bi bi-book-fill"></i><span>题型：单选 + 多选 + 简答（共10题）</span></div>
        </div>
    </div>
</body>
</html>
`;

// 根路径 - 统一入口首页
router.get('/', () => {
  return new Response(HOME_HTML, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 学生考试页
router.get('/exam', () => {
  return new Response(getExamHTML(), {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 教师管理页
router.get('/teacher', () => {
  return new Response(getTeacherHTML(), {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 测试API页面
router.get('/test-api', () => {
  return new Response(getTestAPIHTML(), {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 学号验证
router.post('/api/exam/verify', async (request) => {
  try {
    const data = await request.json();
    const studentId = data.student_id;
    const chapter = data.chapter; // 接收章节参数
    
    if (!studentId) {
      return new Response(JSON.stringify({
        success: false,
        message: '请输入学号'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 查询学生
    let result = null;
    try {
      result = await request.env.DB.prepare(
        'SELECT * FROM students WHERE id = ?'
      ).bind(studentId).first();
    } catch (e) {
      console.log('查询学生失败:', e.message);
    }
    
    // 如果没有结果，使用默认账号
    if (!result && studentId === '123456') {
      result = { id: '123456', name: '测试学生', major: '控制工程（测试）' };
    }
    
    if (result) {
      const sessionId = generateSessionId();
      sessions[sessionId] = {
        student: { id: result.id, name: result.name, major: result.major },
        questions: null,
        startTime: Date.now(),
        chapter: chapter // 保存章节信息
      };
      
      return new Response(JSON.stringify({
        success: true,
        message: `验证成功，欢迎 ${result.name} 同学！${chapter ? '（' + chapter + '专题考试）' : ''}`,
        student: { id: result.id, name: result.name, major: result.major },
        session_id: sessionId,
        chapter: chapter
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    return new Response(JSON.stringify({
      success: false,
      message: '学号不存在'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误: ' + error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 开始考试 - 随机抽题
router.post('/api/exam/start', async (request) => {
  try {
    const data = await request.json();
    const sessionId = data.session_id;
    
    if (!sessionId || !sessions[sessionId]) {
      return new Response(JSON.stringify({
        success: false,
        message: '会话无效'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 获取章节参数（如果有）
    const chapter = sessions[sessionId].chapter;
    
    let singleQuestions, multipleQuestions, shortQuestions;
    
    if (chapter) {
      // 按章节抽题
      singleQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 4'
      ).bind('单选题', chapter).all();
      
      multipleQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 3'
      ).bind('多选题', chapter).all();
      
      shortQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 3'
      ).bind('简答题', chapter).all();
    } else {
      // 从数据库随机抽题（全题库）
      singleQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 4'
      ).bind('单选题').all();
      
      multipleQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 3'
      ).bind('多选题').all();
      
      shortQuestions = await request.env.DB.prepare(
        'SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 3'
      ).bind('简答题').all();
    }
    
    // 合并题目并编号
    const allQuestions = [];
    let seq = 1;
    
    for (const q of singleQuestions.results || []) {
      allQuestions.push({ ...q, seq: seq++ });
    }
    for (const q of multipleQuestions.results || []) {
      allQuestions.push({ ...q, seq: seq++ });
    }
    for (const q of shortQuestions.results || []) {
      allQuestions.push({ ...q, seq: seq++ });
    }
    
    // 保存到会话
    sessions[sessionId].questions = allQuestions;
    sessions[sessionId].startTime = Date.now();
    
    // 返回题目（不包含答案）
    const questionsForClient = allQuestions.map(q => ({
      id: q.id,
      seq: q.seq,
      type: q.type,
      question: q.question,
      options: q.options,
      difficulty: q.difficulty
    }));
    
    return new Response(JSON.stringify({
      success: true,
      questions: questionsForClient,
      total: questionsForClient.length
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误: ' + error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 提交答案
router.post('/api/exam/submit', async (request) => {
  try {
    const data = await request.json();
    const sessionId = data.session_id;
    const answers = data.answers || {};
    
    if (!sessionId || !sessions[sessionId]) {
      return new Response(JSON.stringify({
        success: false,
        message: '会话无效'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    const session = sessions[sessionId];
    const questions = session.questions;
    
    if (!questions || questions.length === 0) {
      return new Response(JSON.stringify({
        success: false,
        message: '未开始考试'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 判分
    let totalScore = 0;
    const results = [];
    
    for (const q of questions) {
      const userAnswer = answers[q.seq] || '';
      const correctAnswer = q.answer;
      let isCorrect = false;
      let score = 0;
      
      if (q.type === '单选题') {
        if (userAnswer === correctAnswer) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === '多选题') {
        // 多选题：答案可能是 ABC 或 ABCD
        const userSet = new Set(String(userAnswer).split('').filter(c => /[A-F]/.test(c)));
        const correctSet = new Set(String(correctAnswer).split('').filter(c => /[A-F]/.test(c)));
        if (userSet.size === correctSet.size && [...userSet].every(x => correctSet.has(x))) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === '简答题') {
        // 简答题：关键词匹配
        const userText = String(userAnswer).toLowerCase();
        const keywords = String(correctAnswer).toLowerCase().split(/[,，。、\s]+/).filter(k => k.length > 2);
        const matched = keywords.filter(k => userText.includes(k)).length;
        const ratio = keywords.length > 0 ? matched / keywords.length : 0;
        
        if (ratio >= 0.6) {
          isCorrect = true;
          score = 10;
        } else if (ratio >= 0.3) {
          score = 5;
        }
      }
      
      totalScore += score;
      
      results.push({
        seq: q.seq,
        id: q.id,
        type: q.type,
        question: q.question,
        options: q.options,
        user_answer: userAnswer,
        correct_answer: correctAnswer,
        is_correct: isCorrect,
        score: score,
        analysis: q.analysis
      });
    }
    
    // 保存考试记录
    const duration = Math.floor((Date.now() - session.startTime) / 1000);
    
    try {
      await request.env.DB.prepare(
        'INSERT INTO exam_records (student_id, student_name, major, score, duration_seconds, start_time, end_time, results) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
      ).bind(
        session.student.id,
        session.student.name,
        session.student.major,
        totalScore,
        duration,
        new Date(session.startTime).toISOString(),
        new Date().toISOString(),
        JSON.stringify(results)
      ).run();
    } catch (e) {
      console.log('保存记录失败:', e.message);
    }
    
    return new Response(JSON.stringify({
      success: true,
      score: totalScore,
      results: results
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误: ' + error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 教师登录
router.post('/api/exam/teacher/login', async (request) => {
  try {
    const data = await request.json();
    const teacherId = data.teacher_id;
    
    if (!teacherId) {
      return new Response(JSON.stringify({
        success: false,
        message: '请输入教师工号'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    let result = null;
    try {
      result = await request.env.DB.prepare(
        'SELECT * FROM students WHERE id = ? AND is_teacher = 1'
      ).bind(teacherId).first();
    } catch (e) {
      console.log('查询教师失败:', e.message);
    }
    
    if (!result && teacherId === '654321') {
      result = { id: '654321', name: '教师管理员', major: '教师', is_teacher: 1 };
    }
    
    if (result) {
      return new Response(JSON.stringify({
        success: true,
        message: '登录成功',
        teacher: {
          id: result.id,
          name: result.name,
          major: result.major,
          is_teacher: true
        }
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    return new Response(JSON.stringify({
      success: false,
      message: '教师工号不存在'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误: ' + error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 获取教师统计数据
router.get('/api/exam/teacher/stats', async (request) => {
  try {
    let totalStudents = 70;
    let examinedCount = 0;
    let avgScore = 0;
    let records = [];
    
    try {
      const totalResult = await request.env.DB.prepare(
        'SELECT COUNT(*) as count FROM students WHERE is_teacher = 0 AND id != ?'
      ).bind('123456').first();
      if (totalResult && totalResult.count) totalStudents = totalResult.count;
    } catch (e) {}
    
    try {
      const examinedResult = await request.env.DB.prepare(
        'SELECT COUNT(DISTINCT student_id) as count FROM exam_records WHERE student_id != ?'
      ).bind('123456').first();
      if (examinedResult && examinedResult.count) examinedCount = examinedResult.count;
    } catch (e) {}
    
    try {
      const avgResult = await request.env.DB.prepare(
        'SELECT AVG(score) as avg_score FROM exam_records WHERE student_id != ?'
      ).bind('123456').first();
      if (avgResult && avgResult.avg_score) avgScore = avgResult.avg_score;
    } catch (e) {}
    
    try {
      const recordsResult = await request.env.DB.prepare(
        'SELECT * FROM exam_records ORDER BY end_time DESC LIMIT 50'
      ).all();
      if (recordsResult && recordsResult.results) records = recordsResult.results;
    } catch (e) {}
    
    return new Response(JSON.stringify({
      success: true,
      stats: {
        total_students: totalStudents,
        examined_count: examinedCount,
        avg_score: avgScore,
        pass_rate: 0
      },
      records: records
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: true,
      stats: { total_students: 70, examined_count: 0, avg_score: 0, pass_rate: 0 },
      records: []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 获取章节列表
router.get('/api/exam/chapters', async (request) => {
  try {
    const result = await request.env.DB.prepare(
      'SELECT chapter, COUNT(*) as count FROM questions GROUP BY chapter ORDER BY chapter'
    ).all();
    
    return new Response(JSON.stringify({
      success: true,
      chapters: result.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '获取章节失败'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// ========== 兼容 dist 前端的 API 路由 ==========

// 兼容：获取章节列表
router.get('/api/chapters', async (request) => {
  try {
    const result = await request.env.DB.prepare(
      'SELECT chapter, COUNT(*) as count FROM questions GROUP BY chapter ORDER BY chapter'
    ).all();
    
    return new Response(JSON.stringify({
      success: true,
      chapters: (result.results || []).map(r => r.chapter)
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '获取章节失败'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 兼容：获取学生列表
router.get('/api/students', async (request) => {
  try {
    const result = await request.env.DB.prepare(
      'SELECT id, name, major FROM students WHERE is_teacher = 0 OR is_teacher IS NULL ORDER BY id LIMIT 100'
    ).all();
    
    return new Response(JSON.stringify({
      success: true,
      students: result.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '获取学生列表失败'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 兼容：获取题目列表
router.get('/api/questions', async (request) => {
  try {
    const url = new URL(request.url);
    const chapter = url.searchParams.get('chapter');
    const limit = parseInt(url.searchParams.get('limit') || '100');
    
    let query = 'SELECT id, type, question, options, answer, chapter, difficulty, analysis FROM questions';
    let params = [];
    
    if (chapter) {
      query += ' WHERE chapter = ?';
      params.push(chapter);
    }
    query += ' ORDER BY RANDOM() LIMIT ?';
    params.push(limit);
    
    const result = await request.env.DB.prepare(query).bind(...params).all();
    
    return new Response(JSON.stringify({
      success: true,
      questions: result.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '获取题目失败: ' + error.message
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 兼容：生成试卷
router.post('/api/generate-exam', async (request) => {
  try {
    const data = await request.json();
    const chapters = data.chapters || [];
    const studentId = data.student_id;
    
    // 查询学生信息
    let student = null;
    try {
      student = await request.env.DB.prepare(
        'SELECT id, name, major FROM students WHERE id = ?'
      ).bind(studentId).first();
    } catch (e) {}
    
    if (!student && studentId === '123456') {
      student = { id: '123456', name: '测试学生', major: '控制工程（测试）' };
    }
    
    if (!student) {
      return new Response(JSON.stringify({
        success: false,
        message: '学生不存在'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 随机抽题
    let query = 'SELECT * FROM questions';
    let params = [];
    
    if (chapters.length > 0) {
      query += ' WHERE chapter IN (' + chapters.map(() => '?').join(',') + ')';
      params = chapters;
    }
    
    // 获取所有符合条件的题目
    const allQuestions = await request.env.DB.prepare(query).bind(...params).all();
    const questions = allQuestions.results || [];
    
    // 按类型分组并随机抽取
    const single = questions.filter(q => q.type === '单选题');
    const multiple = questions.filter(q => q.type === '多选题');
    const short = questions.filter(q => q.type === '简答题');
    
    const shuffle = arr => arr.sort(() => Math.random() - 0.5);
    const selected = [
      ...shuffle(single).slice(0, 4),
      ...shuffle(multiple).slice(0, 3),
      ...shuffle(short).slice(0, 3)
    ];
    
    // 编号
    selected.forEach((q, i) => q.seq = i + 1);
    
    return new Response(JSON.stringify({
      success: true,
      student: student,
      questions: selected.map(q => ({
        id: q.id,
        seq: q.seq,
        type: q.type,
        question: q.question,
        options: q.options,
        chapter: q.chapter,
        difficulty: q.difficulty
      }))
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '生成试卷失败: ' + error.message
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 兼容：提交考试
router.post('/api/submit-exam', async (request) => {
  try {
    const data = await request.json();
    const studentId = data.student_id;
    const studentName = data.student_name;
    const answers = data.answers || {};
    const questions = data.questions || [];
    
    // 判分
    let totalScore = 0;
    const results = [];
    
    for (const q of questions) {
      const userAnswer = answers[q.seq] || '';
      const correctAnswer = q.answer || '';
      let isCorrect = false;
      let score = 0;
      
      if (q.type === '单选题') {
        if (userAnswer === correctAnswer) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === '多选题') {
        const userSet = new Set(String(userAnswer).split('').filter(c => /[A-F]/.test(c)));
        const correctSet = new Set(String(correctAnswer).split('').filter(c => /[A-F]/.test(c)));
        if (userSet.size === correctSet.size && [...userSet].every(x => correctSet.has(x))) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === '简答题') {
        const userText = String(userAnswer).toLowerCase();
        const keywords = String(correctAnswer).toLowerCase().split(/[,，。、\s]+/).filter(k => k.length > 2);
        const matched = keywords.filter(k => userText.includes(k)).length;
        const ratio = keywords.length > 0 ? matched / keywords.length : 0;
        
        if (ratio >= 0.6) {
          isCorrect = true;
          score = 10;
        } else if (ratio >= 0.3) {
          score = 5;
        }
      }
      
      totalScore += score;
      
      results.push({
        seq: q.seq,
        id: q.id,
        type: q.type,
        question: q.question,
        options: q.options,
        user_answer: userAnswer,
        correct_answer: correctAnswer,
        is_correct: isCorrect,
        score: score,
        analysis: q.analysis
      });
    }
    
    // 保存考试记录
    try {
      await request.env.DB.prepare(
        'INSERT INTO exam_records (student_id, student_name, major, score, duration_seconds, start_time, end_time, results) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
      ).bind(
        studentId,
        studentName,
        data.major || '未知专业',
        totalScore,
        data.duration || 0,
        new Date().toISOString(),
        new Date().toISOString(),
        JSON.stringify(results)
      ).run();
    } catch (e) {
      console.log('保存记录失败:', e.message);
    }
    
    return new Response(JSON.stringify({
      success: true,
      score: totalScore,
      results: results
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '提交失败: ' + error.message
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 兼容：获取考试记录
router.get('/api/exam-records', async (request) => {
  try {
    const result = await request.env.DB.prepare(
      'SELECT * FROM exam_records ORDER BY end_time DESC LIMIT 100'
    ).all();
    
    return new Response(JSON.stringify({
      success: true,
      records: result.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '获取记录失败'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 生成章节考试链接
router.get('/api/exam/chapter-link', async (request) => {
  try {
    const url = new URL(request.url);
    const chapter = url.searchParams.get('chapter');
    
    if (!chapter) {
      return new Response(JSON.stringify({
        success: false,
        message: '请指定章节'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 生成唯一链接ID
    const linkId = Math.random().toString(36).substring(2, 10);
    
    // 存储章节考试信息（实际应存入KV，这里简化处理）
    const examLink = `${url.origin}/exam?chapter=${encodeURIComponent(chapter)}&linkId=${linkId}`;
    
    return new Response(JSON.stringify({
      success: true,
      link: examLink,
      chapter: chapter,
      linkId: linkId
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '生成链接失败'
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 生成 session ID
function generateSessionId() {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// 考试页面HTML
function getExamHTML() {
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学生考试 - 火电机组考核系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root{--primary:#1a73e8;--success:#34a853;--danger:#ea4335;--warning:#fbbc04;--bg:#f8f9fa}
        *{box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);margin:0;min-height:100vh}
        .header{background:linear-gradient(135deg,var(--primary) 0%,#1557b0 100%);color:white;padding:15px 0;position:sticky;top:0;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        .header h1{font-size:1.25rem;margin:0}
        .container{max-width:800px;margin:0 auto;padding:15px}
        .card{background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:15px;border:none}
        .card-body{padding:20px}
        .btn-primary{background:var(--primary);border:none;border-radius:8px;padding:12px 24px;font-weight:500}
        .btn-success{background:var(--success);border:none}
        .form-control{border-radius:8px;padding:12px;border:2px solid #e5e7eb}
        .form-control:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(26,115,232,0.1)}
        .question-card{background:#f8fafc;border-radius:12px;padding:20px;margin-bottom:20px;border-left:4px solid var(--primary)}
        .question-num{font-weight:700;color:var(--primary);font-size:18px;margin-bottom:10px}
        .option-item{background:white;border:2px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:10px;cursor:pointer;transition:all 0.2s}
        .option-item:hover{border-color:var(--primary);background:#f0f4ff}
        .option-item.selected{border-color:var(--primary);background:#dbeafe}
        .option-item.correct{border-color:var(--success);background:#d1fae5}
        .option-item.wrong{border-color:var(--danger);background:#fee2e2}
        .result-card{text-align:center;padding:30px}
        .score-circle{width:150px;height:150px;border-radius:50%;background:linear-gradient(135deg,var(--primary) 0%,#1557b0 100%);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;color:white;font-size:48px;font-weight:700}
        .section{display:none}
        .section.active{display:block}
        .progress{height:8px;border-radius:4px}
        .short-input{min-height:100px;resize:vertical}
        .analysis-box{background:#f0f9ff;border-radius:8px;padding:15px;margin-top:15px;border:1px solid #bae6fd;text-align:left}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1><i class="bi bi-lightning-charge-fill"></i> 学生考试</h1>
        </div>
    </div>
    
    <div class="container">
        <!-- 登录页 -->
        <div id="loginSection" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <i class="bi bi-person-circle" style="font-size:80px;color:var(--primary)"></i>
                    <h4 class="mt-3">请输入学号验证身份</h4>
                    <div class="mt-4">
                        <input type="text" class="form-control form-control-lg" id="studentId" placeholder="请输入学号">
                        <button class="btn btn-primary btn-lg w-100 mt-3" onclick="verifyStudent()">
                            <i class="bi bi-box-arrow-in-right me-2"></i>验证登录
                        </button>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> 返回首页</a>
        </div>
        
        <!-- 准备页 -->
        <div id="readySection" class="section">
            <div class="card">
                <div class="card-body text-center">
                    <div class="alert alert-success">
                        <h5>欢迎，<span id="studentName"></span> 同学！</h5>
                        <p class="mb-0">学号：<span id="studentIdDisplay"></span></p>
                    </div>
                    <div class="alert alert-info text-start">
                        <h6><i class="bi bi-info-circle me-2"></i>考试说明</h6>
                        <ul class="mb-0">
                            <li>共 <strong>10</strong> 题（4单选 + 3多选 + 3简答）</li>
                            <li>每题 10 分，满分 100 分</li>
                            <li>提交后可查看答案解析</li>
                        </ul>
                    </div>
                    <button class="btn btn-primary btn-lg w-100" onclick="startExam()">
                        <i class="bi bi-play-circle me-2"></i>开始答题
                    </button>
                </div>
            </div>
        </div>
        
        <!-- 答题页 -->
        <div id="examSection" class="section">
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <span>答题进度</span>
                        <span id="progressText">0 / 10</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar bg-primary" id="progressBar" style="width:0%"></div>
                    </div>
                </div>
            </div>
            
            <div id="questionsContainer"></div>
            
            <button class="btn btn-success btn-lg w-100" onclick="submitExam()">
                <i class="bi bi-check-circle me-2"></i>提交答卷
            </button>
        </div>
        
        <!-- 结果页 -->
        <div id="resultSection" class="section">
            <div class="card">
                <div class="card-body result-card">
                    <div class="score-circle" id="scoreDisplay">0</div>
                    <h4>考试完成</h4>
                    <p class="text-muted">得分：<span id="totalScore">0</span> / 100 分</p>
                </div>
            </div>
            <div id="resultsContainer"></div>
            <div class="mt-3">
                <button class="btn btn-primary" onclick="location.reload()"><i class="bi bi-arrow-repeat"></i> 重新考试</button>
                <a href="/" class="btn btn-outline-secondary ms-2"><i class="bi bi-arrow-left"></i> 返回首页</a>
            </div>
        </div>
    </div>
    
    <script>
        let sessionId = '';
        let questions = [];
        let answers = {};
        let chapter = null; // 章节参数
        
        // 从URL获取章节参数
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            chapter = urlParams.get('chapter');
            
            // 如果有章节参数，显示提示
            if (chapter) {
                const hint = document.createElement('div');
                hint.className = 'alert alert-warning text-center mb-3';
                hint.innerHTML = '<i class="bi bi-book-half me-2"></i>专题考试：<strong>' + chapter + '</strong>';
                document.querySelector('.container').insertBefore(hint, document.querySelector('.container').firstChild);
            }
        };
        
        async function verifyStudent() {
            const studentId = document.getElementById('studentId').value.trim();
            if (!studentId) { alert('请输入学号'); return; }
            
            try {
                const res = await fetch('/api/exam/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        student_id: studentId,
                        chapter: chapter // 传递章节参数
                    })
                });
                const data = await res.json();
                
                if (data.success) {
                    sessionId = data.session_id;
                    document.getElementById('studentName').textContent = data.student.name;
                    document.getElementById('studentIdDisplay').textContent = data.student.id;
                    
                    // 显示章节信息
                    if (data.chapter) {
                        const readySection = document.getElementById('readySection');
                        const chapterAlert = document.createElement('div');
                        chapterAlert.className = 'alert alert-warning text-center';
                        chapterAlert.innerHTML = '<i class="bi bi-book-half me-2"></i>专题考试：<strong>' + data.chapter + '</strong>';
                        readySection.querySelector('.card-body').insertBefore(chapterAlert, readySection.querySelector('.alert-success'));
                    }
                    
                    showSection('readySection');
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('验证失败：' + e.message);
            }
        }
        
        async function startExam() {
            try {
                const res = await fetch('/api/exam/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: sessionId})
                });
                const data = await res.json();
                
                if (data.success) {
                    questions = data.questions;
                    renderQuestions();
                    showSection('examSection');
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('开始考试失败：' + e.message);
            }
        }
        
        function renderQuestions() {
            const container = document.getElementById('questionsContainer');
            container.innerHTML = '';
            
            questions.forEach((q, idx) => {
                const options = q.options ? JSON.parse(q.options) : {};
                let html = '<div class="question-card">';
                html += '<div class="question-num">' + q.seq + '. ' + q.type + '（' + (q.difficulty || '中等') + '）</div>';
                html += '<p>' + q.question + '</p>';
                
                if (q.type === '单选题' || q.type === '多选题') {
                    const isMultiple = q.type === '多选题';
                    for (const [key, val] of Object.entries(options)) {
                        html += '<div class="option-item" onclick="selectOption(' + q.seq + ', \\'' + key + '\\', ' + isMultiple + ')" id="opt-' + q.seq + '-' + key + '">';
                        html += '<strong>' + key + '.</strong> ' + val;
                        html += '</div>';
                    }
                } else {
                    html += '<textarea class="form-control short-input" id="answer-' + q.seq + '" placeholder="请输入答案..." onchange="setAnswer(' + q.seq + ', this.value)"></textarea>';
                }
                
                html += '</div>';
                container.innerHTML += html;
            });
        }
        
        function selectOption(seq, option, isMultiple) {
            if (isMultiple) {
                if (!answers[seq]) answers[seq] = '';
                if (answers[seq].includes(option)) {
                    answers[seq] = answers[seq].replace(option, '');
                } else {
                    answers[seq] += option;
                }
                answers[seq] = answers[seq].split('').sort().join('');
            } else {
                answers[seq] = option;
            }
            
            // 更新UI
            const opts = document.querySelectorAll('[id^="opt-' + seq + '-"]');
            opts.forEach(el => {
                const key = el.id.split('-')[2];
                if (answers[seq] && answers[seq].includes(key)) {
                    el.classList.add('selected');
                } else {
                    el.classList.remove('selected');
                }
            });
            
            updateProgress();
        }
        
        function setAnswer(seq, value) {
            answers[seq] = value;
            updateProgress();
        }
        
        function updateProgress() {
            const answered = Object.keys(answers).filter(k => answers[k]).length;
            document.getElementById('progressText').textContent = answered + ' / ' + questions.length;
            document.getElementById('progressBar').style.width = (answered / questions.length * 100) + '%';
        }
        
        async function submitExam() {
            const answered = Object.keys(answers).filter(k => answers[k]).length;
            if (answered < questions.length) {
                if (!confirm('还有 ' + (questions.length - answered) + ' 题未作答，确定提交吗？')) {
                    return;
                }
            }
            
            try {
                const res = await fetch('/api/exam/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: sessionId, answers: answers})
                });
                const data = await res.json();
                
                if (data.success) {
                    showResults(data);
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('提交失败：' + e.message);
            }
        }
        
        function showResults(data) {
            document.getElementById('scoreDisplay').textContent = data.score;
            document.getElementById('totalScore').textContent = data.score;
            
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '';
            
            data.results.forEach(r => {
                const q = questions.find(x => x.seq === r.seq);
                const options = q && q.options ? JSON.parse(q.options) : {};
                
                let html = '<div class="card mt-3">';
                html += '<div class="card-body">';
                html += '<h6>' + r.seq + '. ' + r.type + ' ' + (r.is_correct ? '✅' : '❌') + '</h6>';
                html += '<p>' + r.question + '</p>';
                
                if (r.type === '单选题' || r.type === '多选题') {
                    for (const [key, val] of Object.entries(options)) {
                        let className = 'option-item';
                        if (r.correct_answer.includes(key)) className += ' correct';
                        if (r.user_answer && r.user_answer.includes(key) && !r.correct_answer.includes(key)) className += ' wrong';
                        
                        html += '<div class="' + className + '" style="cursor:default">';
                        html += '<strong>' + key + '.</strong> ' + val;
                        if (r.correct_answer.includes(key)) html += ' ✓';
                        html += '</div>';
                    }
                }
                
                html += '<p class="mt-2"><strong>你的答案：</strong>' + (r.user_answer || '未作答') + '</p>';
                html += '<p><strong>正确答案：</strong>' + r.correct_answer + '</p>';
                
                if (r.analysis) {
                    html += '<div class="analysis-box"><strong>解析：</strong>' + r.analysis + '</div>';
                }
                
                html += '</div></div>';
                container.innerHTML += html;
            });
            
            showSection('resultSection');
        }
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }
    </script>
</body>
</html>
`;
}

// 教师页面HTML
function getTeacherHTML() {
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>教师管理 - 火电机组考核系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root{--primary:#1a73e8;--success:#34a853;--danger:#ea4335;--warning:#fbbc04;--bg:#f8f9fa}
        *{box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);margin:0;min-height:100vh}
        .header{background:linear-gradient(135deg,var(--success) 0%,#2d8a47 100%);color:white;padding:15px 0;position:sticky;top:0;z-index:100}
        .header h1{font-size:1.25rem;margin:0}
        .container{max-width:1200px;margin:0 auto;padding:15px}
        .card{background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:15px;border:none}
        .card-body{padding:20px}
        .btn-primary{background:var(--primary);border:none;border-radius:8px;padding:12px 24px;font-weight:500}
        .btn-success{background:var(--success);border:none}
        .stat-card{background:linear-gradient(135deg,var(--primary),#1557b0);color:white;border-radius:12px;padding:20px;text-align:center}
        .stat-num{font-size:36px;font-weight:700}
        .stat-label{font-size:14px;opacity:0.9}
        .section{display:none}
        .section.active{display:block}
        .table{margin-bottom:0}
        .table th{background:#f8f9fa;border-bottom:2px solid #dee2e6}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1><i class="bi bi-person-badge-fill"></i> 教师管理后台</h1>
        </div>
    </div>
    
    <div class="container">
        <!-- 登录页 -->
        <div id="loginSection" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <i class="bi bi-shield-lock" style="font-size:80px;color:var(--success)"></i>
                    <h4 class="mt-3">教师登录</h4>
                    <div class="mt-4">
                        <input type="text" class="form-control form-control-lg" id="teacherId" placeholder="请输入教师工号">
                        <button class="btn btn-success btn-lg w-100 mt-3" onclick="teacherLogin()">
                            <i class="bi bi-box-arrow-in-right me-2"></i>登录
                        </button>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> 返回首页</a>
        </div>
        
        <!-- 统计页 -->
        <div id="statsSection" class="section">
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-num" id="totalStudents">70</div>
                        <div class="stat-label">学生总数</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card" style="background:linear-gradient(135deg,var(--success),#2d8a47)">
                        <div class="stat-num" id="examinedCount">0</div>
                        <div class="stat-label">已考试人数</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card" style="background:linear-gradient(135deg,var(--warning),#d97706)">
                        <div class="stat-num" id="avgScore">0</div>
                        <div class="stat-label">平均分</div>
                    </div>
                </div>
            </div>
            
            <!-- 章节出题功能 -->
            <div class="card mb-4">
                <div class="card-body">
                    <h5><i class="bi bi-book-half me-2"></i>章节出题</h5>
                    <p class="text-muted small mb-3">选择章节生成专属考试链接，学生通过该链接只能考所选章节的题目</p>
                    
                    <div class="mb-3">
                        <label class="form-label">选择章节</label>
                        <select class="form-select" id="chapterSelect">
                            <option value="">-- 全题库（不限制章节）--</option>
                        </select>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateChapterLink()">
                        <i class="bi bi-link-45deg me-2"></i>生成考试链接
                    </button>
                    
                    <div id="linkDisplay" class="mt-3" style="display:none">
                        <div class="alert alert-info mb-0">
                            <strong>考试链接：</strong><br>
                            <input type="text" class="form-control mt-2" id="examLink" readonly>
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="copyLink()">
                                <i class="bi bi-clipboard me-1"></i>复制链接
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <h5><i class="bi bi-list-ul me-2"></i>考试记录</h5>
                    <div id="recordsList" class="mt-3 table-responsive">
                        <p class="text-muted text-center">暂无考试记录</p>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary mt-3"><i class="bi bi-arrow-left"></i> 返回首页</a>
        </div>
    </div>
    
    <script>
        async function teacherLogin() {
            const teacherId = document.getElementById('teacherId').value.trim();
            if (!teacherId) { alert('请输入教师工号'); return; }
            
            try {
                const res = await fetch('/api/exam/teacher/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({teacher_id: teacherId})
                });
                const data = await res.json();
                
                if (data.success) {
                    loadStats();
                    showSection('statsSection');
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('登录失败：' + e.message);
            }
        }
        
        async function loadStats() {
            try {
                const res = await fetch('/api/exam/teacher/stats');
                const data = await res.json();
                
                if (data.success) {
                    document.getElementById('totalStudents').textContent = data.stats.total_students;
                    document.getElementById('examinedCount').textContent = data.stats.examined_count;
                    document.getElementById('avgScore').textContent = Math.round(data.stats.avg_score || 0);
                    
                    if (data.records && data.records.length > 0) {
                        let html = '<table class="table"><thead><tr><th>学号</th><th>姓名</th><th>分数</th><th>用时</th><th>时间</th></tr></thead><tbody>';
                        data.records.forEach(r => {
                            const duration = r.duration_seconds ? Math.floor(r.duration_seconds / 60) + '分' : '-';
                            const time = r.end_time ? r.end_time.substring(0, 16).replace('T', ' ') : '-';
                            html += '<tr><td>' + r.student_id + '</td><td>' + (r.student_name || '-') + '</td><td>' + r.score + '</td><td>' + duration + '</td><td>' + time + '</td></tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('recordsList').innerHTML = html;
                    }
                }
            } catch (e) {
                console.error('加载统计失败', e);
            }
            
            // 加载章节列表
            loadChapters();
        }
        
        // 加载章节列表
        async function loadChapters() {
            console.log('开始加载章节列表...');
            try {
                const res = await fetch('/api/exam/chapters');
                const data = await res.json();
                console.log('章节API返回:', data);
                
                if (data.success && data.chapters && data.chapters.length > 0) {
                    const select = document.getElementById('chapterSelect');
                    data.chapters.forEach(ch => {
                        const option = document.createElement('option');
                        option.value = ch.chapter;
                        option.textContent = ch.chapter + ' (' + ch.count + '题)';
                        select.appendChild(option);
                    });
                    console.log('已加载 ' + data.chapters.length + ' 个章节');
                } else {
                    console.log('章节数据为空或加载失败');
                }
            } catch (e) {
                console.error('加载章节失败', e);
            }
        }
        
        // 生成章节考试链接
        async function generateChapterLink() {
            const chapter = document.getElementById('chapterSelect').value;
            
            try {
                const url = '/api/exam/chapter-link' + (chapter ? '?chapter=' + encodeURIComponent(chapter) : '');
                const res = await fetch(url);
                const data = await res.json();
                
                if (data.success) {
                    document.getElementById('examLink').value = data.link;
                    document.getElementById('linkDisplay').style.display = 'block';
                } else {
                    alert('生成链接失败：' + data.message);
                }
            } catch (e) {
                alert('生成链接失败：' + e.message);
            }
        }
        
        // 复制链接
        function copyLink() {
            const linkInput = document.getElementById('examLink');
            linkInput.select();
            document.execCommand('copy');
            alert('链接已复制到剪贴板！');
        }
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }
    </script>
</body>
</html>
`;
}

// 处理 OPTIONS 请求
router.options('*', () => new Response(null, { headers: corsHeaders }));

// 404 处理
router.all('*', () => new Response('Not Found', { status: 404 }));

// 导出
export default {
  async fetch(request, env, ctx) {
    return router.handle(request, env, ctx);
  }
};
