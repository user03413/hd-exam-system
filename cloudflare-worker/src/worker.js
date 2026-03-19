// 火电机组考核系统 - Cloudflare Workers 后端

import { Router } from 'itty-router';

const router = Router();

// CORS 头
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// 根路径欢迎页
router.get('/', () => {
  return new Response(`
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>火电机组考核系统 API</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
    .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
    .api { margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #1a73e8; }
    .method { display: inline-block; padding: 3px 10px; background: #1a73e8; color: white; border-radius: 3px; font-size: 12px; margin-right: 10px; }
    code { background: #e3f2fd; padding: 2px 6px; border-radius: 3px; }
    .status { color: #34a853; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔥 火电机组考核系统 API</h1>
    <p><span class="status">✅ 服务运行正常</span></p>
    
    <h2>📋 可用接口</h2>
    
    <div class="api">
      <h3>学生验证</h3>
      <p><span class="method">POST</span> <code>/api/exam/verify</code></p>
      <p>请求体: <code>{"student_id": "123456"}</code></p>
    </div>
    
    <div class="api">
      <h3>教师登录</h3>
      <p><span class="method">POST</span> <code>/api/exam/teacher/login</code></p>
      <p>请求体: <code>{"teacher_id": "654321"}</code></p>
    </div>
    
    <div class="api">
      <h3>统计信息</h3>
      <p><span class="method">GET</span> <code>/api/exam/teacher/stats</code></p>
    </div>
    
    <h2>🌐 访问地址</h2>
    <p>学生考试: <a href="https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/exam">点击访问</a></p>
    <p>教师后台: <a href="https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/teacher">点击访问</a></p>
  </div>
</body>
</html>
  `, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
  });
});

// 学生数据（从环境变量或 KV 存储）
const STUDENTS = {
  '123456': { id: '123456', name: '测试学生', major: '控制工程（测试）' },
  '654321': { id: '654321', name: '教师管理员', major: '教师', is_teacher: true },
  // 实际使用时会从 D1 数据库加载
};

// 学号验证
router.post('/api/exam/verify', async (request) => {
  try {
    const data = await request.json();
    const studentId = data.student_id;
    
    // 从 D1 数据库查询
    const result = await request.env.DB.prepare(
      'SELECT * FROM students WHERE id = ?'
    ).bind(studentId).first();
    
    if (result) {
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
    } else {
      return new Response(JSON.stringify({
        success: false,
        message: '学号不存在'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误'
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
    
    const result = await request.env.DB.prepare(
      'SELECT * FROM students WHERE id = ? AND is_teacher = 1'
    ).bind(teacherId).first();
    
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
    } else {
      return new Response(JSON.stringify({
        success: false,
        message: '教师工号不存在'
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误'
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
    const totalResult = await request.env.DB.prepare(
      'SELECT COUNT(*) as count FROM students WHERE is_teacher = 0 AND id != ?'
    ).bind('123456').first();
    
    // 统计已考试学生数
    const examinedResult = await request.env.DB.prepare(
      'SELECT COUNT(DISTINCT student_id) as count FROM exam_records WHERE student_id != ?'
    ).bind('123456').first();
    
    // 获取平均分
    const avgResult = await request.env.DB.prepare(
      'SELECT AVG(score) as avg_score FROM exam_records WHERE student_id != ?'
    ).bind('123456').first();
    
    // 获取考试记录
    const records = await request.env.DB.prepare(
      'SELECT * FROM exam_records ORDER BY end_time DESC LIMIT 50'
    ).all();
    
    return new Response(JSON.stringify({
      success: true,
      stats: {
        total_students: totalResult.count || 70,
        examined_count: examinedResult.count || 0,
        avg_score: avgResult.avg_score || 0,
        pass_rate: 0
      },
      records: records.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: '服务器错误'
    }), {
      status: 500,
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
