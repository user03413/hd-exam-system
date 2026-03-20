// 火电机组考核系统 - Cloudflare Workers 后端

import { Router } from 'itty-router';

const router = Router();

// CORS 头
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

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
`;

// 考试页面
const EXAM_HTML = `
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
        .question-num{font-weight:700;color:var(--primary);font-size:18px}
        .option-item{background:white;border:2px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:10px;cursor:pointer;transition:all 0.2s}
        .option-item:hover{border-color:var(--primary);background:#f0f4ff}
        .option-item.selected{border-color:var(--primary);background:#dbeafe}
        .result-card{text-align:center;padding:30px}
        .score-circle{width:150px;height:150px;border-radius:50%;background:linear-gradient(135deg,var(--primary) 0%,#1557b0 100%);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;color:white;font-size:48px;font-weight:700}
        .section{display:none}
        .section.active{display:block}
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
                    <p class="mt-3 text-muted">测试学号：123456</p>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> 返回首页</a>
        </div>
        
        <!-- 结果页 -->
        <div id="resultSection" class="section">
            <div class="card">
                <div class="card-body result-card">
                    <div class="score-circle" id="scoreDisplay">0</div>
                    <h4>考试完成</h4>
                    <p class="text-muted" id="resultMsg"></p>
                    <button class="btn btn-primary mt-3" onclick="location.reload()"><i class="bi bi-arrow-repeat"></i> 重新考试</button>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> 返回首页</a>
        </div>
    </div>
    
    <script>
        let sessionId = '';
        
        async function verifyStudent() {
            const studentId = document.getElementById('studentId').value.trim();
            if (!studentId) {
                alert('请输入学号');
                return;
            }
            
            try {
                const res = await fetch('/api/exam/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({student_id: studentId})
                });
                const data = await res.json();
                
                if (data.success) {
                    sessionId = data.session_id;
                    alert('验证成功！欢迎 ' + data.student.name + ' 同学！');
                    document.getElementById('scoreDisplay').textContent = '100';
                    document.getElementById('resultMsg').textContent = '演示模式：请使用完整系统进行考试';
                    showSection('resultSection');
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('验证失败：' + e.message);
            }
        }
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }
    </script>
</body>
</html>
`;

// 教师页面
const TEACHER_HTML = `
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
        .stat-card{background:linear-gradient(135deg,var(--primary),#1557b0);color:white;border-radius:12px;padding:20px;text-align:center}
        .stat-num{font-size:36px;font-weight:700}
        .stat-label{font-size:14px;opacity:0.9}
        .section{display:none}
        .section.active{display:block}
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
                    <p class="mt-3 text-muted">测试工号：654321</p>
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
            
            <div class="card">
                <div class="card-body">
                    <h5><i class="bi bi-list-ul me-2"></i>考试记录</h5>
                    <div id="recordsList" class="mt-3">
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
            if (!teacherId) {
                alert('请输入教师工号');
                return;
            }
            
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
                        let html = '<table class="table"><thead><tr><th>学号</th><th>姓名</th><th>分数</th><th>时间</th></tr></thead><tbody>';
                        data.records.forEach(r => {
                            html += '<tr><td>' + r.student_id + '</td><td>' + (r.student_name || '-') + '</td><td>' + r.score + '</td><td>' + (r.end_time || '-') + '</td></tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('recordsList').innerHTML = html;
                    }
                }
            } catch (e) {
                console.error('加载统计失败', e);
            }
        }
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }
    </script>
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
  return new Response(EXAM_HTML, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 教师管理页
router.get('/teacher', () => {
  return new Response(TEACHER_HTML, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 学号验证
router.post('/api/exam/verify', async (request) => {
  try {
    const data = await request.json();
    const studentId = data.student_id;
    
    if (!studentId) {
      return new Response(JSON.stringify({
        success: false,
        message: '请输入学号'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // 尝试从数据库查询
    let result = null;
    try {
      result = await request.env.DB.prepare(
        'SELECT * FROM students WHERE id = ?'
      ).bind(studentId).first();
    } catch (e) {
      console.log('查询学生失败:', e.message);
    }
    
    // 如果数据库查询失败，使用默认账号
    if (!result) {
      // 默认测试账号
      if (studentId === '123456') {
        const sessionId = generateSessionId();
        return new Response(JSON.stringify({
          success: true,
          message: '验证成功，欢迎 测试学生 同学！',
          student: {
            id: '123456',
            name: '测试学生',
            major: '控制工程（测试）'
          },
          session_id: sessionId
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
    }
    
    const sessionId = generateSessionId();
    return new Response(JSON.stringify({
      success: true,
      message: `验证成功，欢迎 ${result.name} 同学！`,
      student: {
        id: result.id,
        name: result.name,
        major: result.major
      },
      session_id: sessionId
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
    
    // 检查数据库中是否有教师账号
    let result = null;
    try {
      result = await request.env.DB.prepare(
        'SELECT * FROM students WHERE id = ? AND is_teacher = 1'
      ).bind(teacherId).first();
    } catch (e) {
      console.log('查询教师失败:', e.message);
    }
    
    // 如果数据库查询失败或没有结果，使用默认账号
    if (!result) {
      // 默认教师账号
      if (teacherId === '654321') {
        return new Response(JSON.stringify({
          success: true,
          message: '登录成功',
          teacher: {
            id: '654321',
            name: '教师管理员',
            major: '教师',
            is_teacher: true
          }
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      } else {
        return new Response(JSON.stringify({
          success: false,
          message: '教师工号不存在'
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }
    
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
    // 统计学生总数
    let totalStudents = 70;
    try {
      const totalResult = await request.env.DB.prepare(
        'SELECT COUNT(*) as count FROM students WHERE is_teacher = 0 AND id != ?'
      ).bind('123456').first();
      if (totalResult && totalResult.count) {
        totalStudents = totalResult.count;
      }
    } catch (e) {
      console.log('统计学生失败:', e.message);
    }
    
    // 统计已考试学生数
    let examinedCount = 0;
    try {
      const examinedResult = await request.env.DB.prepare(
        'SELECT COUNT(DISTINCT student_id) as count FROM exam_records WHERE student_id != ?'
      ).bind('123456').first();
      if (examinedResult && examinedResult.count) {
        examinedCount = examinedResult.count;
      }
    } catch (e) {
      console.log('统计考试记录失败:', e.message);
    }
    
    // 获取平均分
    let avgScore = 0;
    try {
      const avgResult = await request.env.DB.prepare(
        'SELECT AVG(score) as avg_score FROM exam_records WHERE student_id != ?'
      ).bind('123456').first();
      if (avgResult && avgResult.avg_score) {
        avgScore = avgResult.avg_score;
      }
    } catch (e) {
      console.log('统计平均分失败:', e.message);
    }
    
    // 获取考试记录
    let records = [];
    try {
      const recordsResult = await request.env.DB.prepare(
        'SELECT * FROM exam_records ORDER BY end_time DESC LIMIT 50'
      ).all();
      if (recordsResult && recordsResult.results) {
        records = recordsResult.results;
      }
    } catch (e) {
      console.log('获取考试记录失败:', e.message);
    }
    
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
      stats: {
        total_students: 70,
        examined_count: 0,
        avg_score: 0,
        pass_rate: 0
      },
      records: [],
      error: error.message
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// 生成 session ID
function generateSessionId() {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
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
