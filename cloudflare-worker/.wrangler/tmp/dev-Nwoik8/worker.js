var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// .wrangler/tmp/bundle-wgObnX/checked-fetch.js
var urls = /* @__PURE__ */ new Set();
function checkURL(request, init) {
  const url = request instanceof URL ? request : new URL(
    (typeof request === "string" ? new Request(request, init) : request).url
  );
  if (url.port && url.port !== "443" && url.protocol === "https:") {
    if (!urls.has(url.toString())) {
      urls.add(url.toString());
      console.warn(
        `WARNING: known issue with \`fetch()\` requests to custom HTTPS ports in published Workers:
 - ${url.toString()} - the custom port will be ignored when the Worker is published using the \`wrangler deploy\` command.
`
      );
    }
  }
}
__name(checkURL, "checkURL");
globalThis.fetch = new Proxy(globalThis.fetch, {
  apply(target, thisArg, argArray) {
    const [request, init] = argArray;
    checkURL(request, init);
    return Reflect.apply(target, thisArg, argArray);
  }
});

// node_modules/itty-router/index.mjs
var e = /* @__PURE__ */ __name(({ base: e2 = "", routes: t = [], ...o2 } = {}) => ({ __proto__: new Proxy({}, { get: /* @__PURE__ */ __name((o3, s2, r, n) => "handle" == s2 ? r.fetch : (o4, ...a) => t.push([s2.toUpperCase?.(), RegExp(`^${(n = (e2 + o4).replace(/\/+(\/|$)/g, "$1")).replace(/(\/?\.?):(\w+)\+/g, "($1(?<$2>*))").replace(/(\/?\.?):(\w+)/g, "($1(?<$2>[^$1/]+?))").replace(/\./g, "\\.").replace(/(\/?)\*/g, "($1.*)?")}/*$`), a, n]) && r, "get") }), routes: t, ...o2, async fetch(e3, ...o3) {
  let s2, r, n = new URL(e3.url), a = e3.query = { __proto__: null };
  for (let [e4, t2] of n.searchParams) a[e4] = a[e4] ? [].concat(a[e4], t2) : t2;
  for (let [a2, c2, i2, l2] of t) if ((a2 == e3.method || "ALL" == a2) && (r = n.pathname.match(c2))) {
    e3.params = r.groups || {}, e3.route = l2;
    for (let t2 of i2) if (null != (s2 = await t2(e3.proxy ?? e3, ...o3))) return s2;
  }
} }), "e");
var o = /* @__PURE__ */ __name((e2 = "text/plain; charset=utf-8", t) => (o2, { headers: s2 = {}, ...r } = {}) => void 0 === o2 || "Response" === o2?.constructor.name ? o2 : new Response(t ? t(o2) : o2, { headers: { "content-type": e2, ...s2.entries ? Object.fromEntries(s2) : s2 }, ...r }), "o");
var s = o("application/json; charset=utf-8", JSON.stringify);
var c = o("text/plain; charset=utf-8", String);
var i = o("text/html");
var l = o("image/jpeg");
var p = o("image/png");
var d = o("image/webp");

// src/worker.js
var router = e();
var corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};
var sessions = {};
var HOME_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>\u706B\u7535\u673A\u7EC4\u8003\u6838\u7CFB\u7EDF</title>
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
        <h1>\u706B\u7535\u673A\u7EC4\u8003\u6838\u7CFB\u7EDF</h1>
        <p class="subtitle">\u57FA\u4E8E\u300A\u706B\u7535\u5382\u70ED\u5DE5\u81EA\u52A8\u63A7\u5236\u6280\u672F\u53CA\u5E94\u7528\u300B\u6559\u6750</p>
        <div class="entry-cards">
            <a href="exam" class="entry-card student-card">
                <div class="card-icon"><i class="bi bi-mortarboard-fill"></i></div>
                <div class="card-title">\u5B66\u751F\u8003\u8BD5\u5165\u53E3</div>
                <div class="card-desc">\u5B66\u53F7\u9A8C\u8BC1 \u2192 \u968F\u673A\u62BD\u9898 \u2192 \u5728\u7EBF\u7B54\u9898 \u2192 \u81EA\u52A8\u5224\u5206</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
            <a href="teacher" class="entry-card teacher-card">
                <div class="card-icon"><i class="bi bi-person-badge-fill"></i></div>
                <div class="card-title">\u6559\u5E08\u7BA1\u7406\u5165\u53E3</div>
                <div class="card-desc">\u67E5\u770B\u7EDF\u8BA1 \xB7 \u8003\u8BD5\u8BB0\u5F55 \xB7 \u6570\u636E\u5206\u6790 \xB7 \u6210\u7EE9\u7BA1\u7406</div>
                <i class="bi bi-arrow-right card-arrow"></i>
            </a>
        </div>
        <div class="info-box">
            <div class="info-item"><i class="bi bi-people-fill"></i><span>\u9898\u5E93\uFF1A244\u9898 \xB7 \u5B66\u751F\uFF1A70\u4EBA</span></div>
            <div class="info-item"><i class="bi bi-book-fill"></i><span>\u9898\u578B\uFF1A\u5355\u9009 + \u591A\u9009 + \u7B80\u7B54\uFF08\u517110\u9898\uFF09</span></div>
        </div>
    </div>
</body>
</html>
`;
router.get("/", () => {
  return new Response(HOME_HTML, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders }
  });
});
router.get("/exam", () => {
  return new Response(getExamHTML(), {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders }
  });
});
router.get("/teacher", () => {
  return new Response(getTeacherHTML(), {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders }
  });
});
router.post("/api/exam/verify", async (request) => {
  try {
    const data = await request.json();
    const studentId = data.student_id;
    const chapter = data.chapter;
    if (!studentId) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u8BF7\u8F93\u5165\u5B66\u53F7"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    let result = null;
    try {
      result = await request.env.DB.prepare(
        "SELECT * FROM students WHERE id = ?"
      ).bind(studentId).first();
    } catch (e2) {
      console.log("\u67E5\u8BE2\u5B66\u751F\u5931\u8D25:", e2.message);
    }
    if (!result && studentId === "123456") {
      result = { id: "123456", name: "\u6D4B\u8BD5\u5B66\u751F", major: "\u63A7\u5236\u5DE5\u7A0B\uFF08\u6D4B\u8BD5\uFF09" };
    }
    if (result) {
      const sessionId = generateSessionId();
      sessions[sessionId] = {
        student: { id: result.id, name: result.name, major: result.major },
        questions: null,
        startTime: Date.now(),
        chapter
        // 保存章节信息
      };
      return new Response(JSON.stringify({
        success: true,
        message: `\u9A8C\u8BC1\u6210\u529F\uFF0C\u6B22\u8FCE ${result.name} \u540C\u5B66\uFF01${chapter ? "\uFF08" + chapter + "\u4E13\u9898\u8003\u8BD5\uFF09" : ""}`,
        student: { id: result.id, name: result.name, major: result.major },
        session_id: sessionId,
        chapter
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    return new Response(JSON.stringify({
      success: false,
      message: "\u5B66\u53F7\u4E0D\u5B58\u5728"
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u670D\u52A1\u5668\u9519\u8BEF: " + error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.post("/api/exam/start", async (request) => {
  try {
    const data = await request.json();
    const sessionId = data.session_id;
    if (!sessionId || !sessions[sessionId]) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u4F1A\u8BDD\u65E0\u6548"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    const chapter = sessions[sessionId].chapter;
    let singleQuestions, multipleQuestions, shortQuestions;
    if (chapter) {
      singleQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 4"
      ).bind("\u5355\u9009\u9898", chapter).all();
      multipleQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 3"
      ).bind("\u591A\u9009\u9898", chapter).all();
      shortQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? AND chapter = ? ORDER BY RANDOM() LIMIT 3"
      ).bind("\u7B80\u7B54\u9898", chapter).all();
    } else {
      singleQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 4"
      ).bind("\u5355\u9009\u9898").all();
      multipleQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 3"
      ).bind("\u591A\u9009\u9898").all();
      shortQuestions = await request.env.DB.prepare(
        "SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT 3"
      ).bind("\u7B80\u7B54\u9898").all();
    }
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
    sessions[sessionId].questions = allQuestions;
    sessions[sessionId].startTime = Date.now();
    const questionsForClient = allQuestions.map((q) => ({
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
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u670D\u52A1\u5668\u9519\u8BEF: " + error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.post("/api/exam/submit", async (request) => {
  try {
    const data = await request.json();
    const sessionId = data.session_id;
    const answers = data.answers || {};
    if (!sessionId || !sessions[sessionId]) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u4F1A\u8BDD\u65E0\u6548"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    const session = sessions[sessionId];
    const questions = session.questions;
    if (!questions || questions.length === 0) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u672A\u5F00\u59CB\u8003\u8BD5"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    let totalScore = 0;
    const results = [];
    for (const q of questions) {
      const userAnswer = answers[q.seq] || "";
      const correctAnswer = q.answer;
      let isCorrect = false;
      let score = 0;
      if (q.type === "\u5355\u9009\u9898") {
        if (userAnswer === correctAnswer) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === "\u591A\u9009\u9898") {
        const userSet = new Set(String(userAnswer).split("").filter((c2) => /[A-F]/.test(c2)));
        const correctSet = new Set(String(correctAnswer).split("").filter((c2) => /[A-F]/.test(c2)));
        if (userSet.size === correctSet.size && [...userSet].every((x) => correctSet.has(x))) {
          isCorrect = true;
          score = 10;
        }
      } else if (q.type === "\u7B80\u7B54\u9898") {
        const userText = String(userAnswer).toLowerCase();
        const keywords = String(correctAnswer).toLowerCase().split(/[,，。、\s]+/).filter((k) => k.length > 2);
        const matched = keywords.filter((k) => userText.includes(k)).length;
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
        score,
        analysis: q.analysis
      });
    }
    const duration = Math.floor((Date.now() - session.startTime) / 1e3);
    try {
      await request.env.DB.prepare(
        "INSERT INTO exam_records (student_id, student_name, major, score, duration_seconds, start_time, end_time, results) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
      ).bind(
        session.student.id,
        session.student.name,
        session.student.major,
        totalScore,
        duration,
        new Date(session.startTime).toISOString(),
        (/* @__PURE__ */ new Date()).toISOString(),
        JSON.stringify(results)
      ).run();
    } catch (e2) {
      console.log("\u4FDD\u5B58\u8BB0\u5F55\u5931\u8D25:", e2.message);
    }
    return new Response(JSON.stringify({
      success: true,
      score: totalScore,
      results
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u670D\u52A1\u5668\u9519\u8BEF: " + error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.post("/api/exam/teacher/login", async (request) => {
  try {
    const data = await request.json();
    const teacherId = data.teacher_id;
    if (!teacherId) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u8BF7\u8F93\u5165\u6559\u5E08\u5DE5\u53F7"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    let result = null;
    try {
      result = await request.env.DB.prepare(
        "SELECT * FROM students WHERE id = ? AND is_teacher = 1"
      ).bind(teacherId).first();
    } catch (e2) {
      console.log("\u67E5\u8BE2\u6559\u5E08\u5931\u8D25:", e2.message);
    }
    if (!result && teacherId === "654321") {
      result = { id: "654321", name: "\u6559\u5E08\u7BA1\u7406\u5458", major: "\u6559\u5E08", is_teacher: 1 };
    }
    if (result) {
      return new Response(JSON.stringify({
        success: true,
        message: "\u767B\u5F55\u6210\u529F",
        teacher: {
          id: result.id,
          name: result.name,
          major: result.major,
          is_teacher: true
        }
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    return new Response(JSON.stringify({
      success: false,
      message: "\u6559\u5E08\u5DE5\u53F7\u4E0D\u5B58\u5728"
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u670D\u52A1\u5668\u9519\u8BEF: " + error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.get("/api/exam/teacher/stats", async (request) => {
  try {
    let totalStudents = 70;
    let examinedCount = 0;
    let avgScore = 0;
    let records = [];
    try {
      const totalResult = await request.env.DB.prepare(
        "SELECT COUNT(*) as count FROM students WHERE is_teacher = 0 AND id != ?"
      ).bind("123456").first();
      if (totalResult && totalResult.count) totalStudents = totalResult.count;
    } catch (e2) {
    }
    try {
      const examinedResult = await request.env.DB.prepare(
        "SELECT COUNT(DISTINCT student_id) as count FROM exam_records WHERE student_id != ?"
      ).bind("123456").first();
      if (examinedResult && examinedResult.count) examinedCount = examinedResult.count;
    } catch (e2) {
    }
    try {
      const avgResult = await request.env.DB.prepare(
        "SELECT AVG(score) as avg_score FROM exam_records WHERE student_id != ?"
      ).bind("123456").first();
      if (avgResult && avgResult.avg_score) avgScore = avgResult.avg_score;
    } catch (e2) {
    }
    try {
      const recordsResult = await request.env.DB.prepare(
        "SELECT * FROM exam_records ORDER BY end_time DESC LIMIT 50"
      ).all();
      if (recordsResult && recordsResult.results) records = recordsResult.results;
    } catch (e2) {
    }
    return new Response(JSON.stringify({
      success: true,
      stats: {
        total_students: totalStudents,
        examined_count: examinedCount,
        avg_score: avgScore,
        pass_rate: 0
      },
      records
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: true,
      stats: { total_students: 70, examined_count: 0, avg_score: 0, pass_rate: 0 },
      records: []
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.get("/api/exam/chapters", async (request) => {
  try {
    const result = await request.env.DB.prepare(
      "SELECT chapter, COUNT(*) as count FROM questions GROUP BY chapter ORDER BY chapter"
    ).all();
    return new Response(JSON.stringify({
      success: true,
      chapters: result.results || []
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u83B7\u53D6\u7AE0\u8282\u5931\u8D25"
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
router.get("/api/exam/chapter-link", async (request) => {
  try {
    const url = new URL(request.url);
    const chapter = url.searchParams.get("chapter");
    if (!chapter) {
      return new Response(JSON.stringify({
        success: false,
        message: "\u8BF7\u6307\u5B9A\u7AE0\u8282"
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
    const linkId = Math.random().toString(36).substring(2, 10);
    const examLink = `${url.origin}/exam?chapter=${encodeURIComponent(chapter)}&linkId=${linkId}`;
    return new Response(JSON.stringify({
      success: true,
      link: examLink,
      chapter,
      linkId
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      message: "\u751F\u6210\u94FE\u63A5\u5931\u8D25"
    }), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
});
function generateSessionId() {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}
__name(generateSessionId, "generateSessionId");
function getExamHTML() {
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>\u5B66\u751F\u8003\u8BD5 - \u706B\u7535\u673A\u7EC4\u8003\u6838\u7CFB\u7EDF</title>
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
            <h1><i class="bi bi-lightning-charge-fill"></i> \u5B66\u751F\u8003\u8BD5</h1>
        </div>
    </div>
    
    <div class="container">
        <!-- \u767B\u5F55\u9875 -->
        <div id="loginSection" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <i class="bi bi-person-circle" style="font-size:80px;color:var(--primary)"></i>
                    <h4 class="mt-3">\u8BF7\u8F93\u5165\u5B66\u53F7\u9A8C\u8BC1\u8EAB\u4EFD</h4>
                    <div class="mt-4">
                        <input type="text" class="form-control form-control-lg" id="studentId" placeholder="\u8BF7\u8F93\u5165\u5B66\u53F7">
                        <button class="btn btn-primary btn-lg w-100 mt-3" onclick="verifyStudent()">
                            <i class="bi bi-box-arrow-in-right me-2"></i>\u9A8C\u8BC1\u767B\u5F55
                        </button>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> \u8FD4\u56DE\u9996\u9875</a>
        </div>
        
        <!-- \u51C6\u5907\u9875 -->
        <div id="readySection" class="section">
            <div class="card">
                <div class="card-body text-center">
                    <div class="alert alert-success">
                        <h5>\u6B22\u8FCE\uFF0C<span id="studentName"></span> \u540C\u5B66\uFF01</h5>
                        <p class="mb-0">\u5B66\u53F7\uFF1A<span id="studentIdDisplay"></span></p>
                    </div>
                    <div class="alert alert-info text-start">
                        <h6><i class="bi bi-info-circle me-2"></i>\u8003\u8BD5\u8BF4\u660E</h6>
                        <ul class="mb-0">
                            <li>\u5171 <strong>10</strong> \u9898\uFF084\u5355\u9009 + 3\u591A\u9009 + 3\u7B80\u7B54\uFF09</li>
                            <li>\u6BCF\u9898 10 \u5206\uFF0C\u6EE1\u5206 100 \u5206</li>
                            <li>\u63D0\u4EA4\u540E\u53EF\u67E5\u770B\u7B54\u6848\u89E3\u6790</li>
                        </ul>
                    </div>
                    <button class="btn btn-primary btn-lg w-100" onclick="startExam()">
                        <i class="bi bi-play-circle me-2"></i>\u5F00\u59CB\u7B54\u9898
                    </button>
                </div>
            </div>
        </div>
        
        <!-- \u7B54\u9898\u9875 -->
        <div id="examSection" class="section">
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <span>\u7B54\u9898\u8FDB\u5EA6</span>
                        <span id="progressText">0 / 10</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar bg-primary" id="progressBar" style="width:0%"></div>
                    </div>
                </div>
            </div>
            
            <div id="questionsContainer"></div>
            
            <button class="btn btn-success btn-lg w-100" onclick="submitExam()">
                <i class="bi bi-check-circle me-2"></i>\u63D0\u4EA4\u7B54\u5377
            </button>
        </div>
        
        <!-- \u7ED3\u679C\u9875 -->
        <div id="resultSection" class="section">
            <div class="card">
                <div class="card-body result-card">
                    <div class="score-circle" id="scoreDisplay">0</div>
                    <h4>\u8003\u8BD5\u5B8C\u6210</h4>
                    <p class="text-muted">\u5F97\u5206\uFF1A<span id="totalScore">0</span> / 100 \u5206</p>
                </div>
            </div>
            <div id="resultsContainer"></div>
            <div class="mt-3">
                <button class="btn btn-primary" onclick="location.reload()"><i class="bi bi-arrow-repeat"></i> \u91CD\u65B0\u8003\u8BD5</button>
                <a href="/" class="btn btn-outline-secondary ms-2"><i class="bi bi-arrow-left"></i> \u8FD4\u56DE\u9996\u9875</a>
            </div>
        </div>
    </div>
    
    <script>
        let sessionId = '';
        let questions = [];
        let answers = {};
        let chapter = null; // \u7AE0\u8282\u53C2\u6570
        
        // \u4ECEURL\u83B7\u53D6\u7AE0\u8282\u53C2\u6570
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            chapter = urlParams.get('chapter');
            
            // \u5982\u679C\u6709\u7AE0\u8282\u53C2\u6570\uFF0C\u663E\u793A\u63D0\u793A
            if (chapter) {
                const hint = document.createElement('div');
                hint.className = 'alert alert-warning text-center mb-3';
                hint.innerHTML = '<i class="bi bi-book-half me-2"></i>\u4E13\u9898\u8003\u8BD5\uFF1A<strong>' + chapter + '</strong>';
                document.querySelector('.container').insertBefore(hint, document.querySelector('.container').firstChild);
            }
        };
        
        async function verifyStudent() {
            const studentId = document.getElementById('studentId').value.trim();
            if (!studentId) { alert('\u8BF7\u8F93\u5165\u5B66\u53F7'); return; }
            
            try {
                const res = await fetch('/api/exam/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        student_id: studentId,
                        chapter: chapter // \u4F20\u9012\u7AE0\u8282\u53C2\u6570
                    })
                });
                const data = await res.json();
                
                if (data.success) {
                    sessionId = data.session_id;
                    document.getElementById('studentName').textContent = data.student.name;
                    document.getElementById('studentIdDisplay').textContent = data.student.id;
                    
                    // \u663E\u793A\u7AE0\u8282\u4FE1\u606F
                    if (data.chapter) {
                        const readySection = document.getElementById('readySection');
                        const chapterAlert = document.createElement('div');
                        chapterAlert.className = 'alert alert-warning text-center';
                        chapterAlert.innerHTML = '<i class="bi bi-book-half me-2"></i>\u4E13\u9898\u8003\u8BD5\uFF1A<strong>' + data.chapter + '</strong>';
                        readySection.querySelector('.card-body').insertBefore(chapterAlert, readySection.querySelector('.alert-success'));
                    }
                    
                    showSection('readySection');
                } else {
                    alert(data.message);
                }
            } catch (e) {
                alert('\u9A8C\u8BC1\u5931\u8D25\uFF1A' + e.message);
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
                alert('\u5F00\u59CB\u8003\u8BD5\u5931\u8D25\uFF1A' + e.message);
            }
        }
        
        function renderQuestions() {
            const container = document.getElementById('questionsContainer');
            container.innerHTML = '';
            
            questions.forEach((q, idx) => {
                const options = q.options ? JSON.parse(q.options) : {};
                let html = '<div class="question-card">';
                html += '<div class="question-num">' + q.seq + '. ' + q.type + '\uFF08' + (q.difficulty || '\u4E2D\u7B49') + '\uFF09</div>';
                html += '<p>' + q.question + '</p>';
                
                if (q.type === '\u5355\u9009\u9898' || q.type === '\u591A\u9009\u9898') {
                    const isMultiple = q.type === '\u591A\u9009\u9898';
                    for (const [key, val] of Object.entries(options)) {
                        html += '<div class="option-item" onclick="selectOption(' + q.seq + ', \\'' + key + '\\', ' + isMultiple + ')" id="opt-' + q.seq + '-' + key + '">';
                        html += '<strong>' + key + '.</strong> ' + val;
                        html += '</div>';
                    }
                } else {
                    html += '<textarea class="form-control short-input" id="answer-' + q.seq + '" placeholder="\u8BF7\u8F93\u5165\u7B54\u6848..." onchange="setAnswer(' + q.seq + ', this.value)"></textarea>';
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
            
            // \u66F4\u65B0UI
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
                if (!confirm('\u8FD8\u6709 ' + (questions.length - answered) + ' \u9898\u672A\u4F5C\u7B54\uFF0C\u786E\u5B9A\u63D0\u4EA4\u5417\uFF1F')) {
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
                alert('\u63D0\u4EA4\u5931\u8D25\uFF1A' + e.message);
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
                html += '<h6>' + r.seq + '. ' + r.type + ' ' + (r.is_correct ? '\u2705' : '\u274C') + '</h6>';
                html += '<p>' + r.question + '</p>';
                
                if (r.type === '\u5355\u9009\u9898' || r.type === '\u591A\u9009\u9898') {
                    for (const [key, val] of Object.entries(options)) {
                        let className = 'option-item';
                        if (r.correct_answer.includes(key)) className += ' correct';
                        if (r.user_answer && r.user_answer.includes(key) && !r.correct_answer.includes(key)) className += ' wrong';
                        
                        html += '<div class="' + className + '" style="cursor:default">';
                        html += '<strong>' + key + '.</strong> ' + val;
                        if (r.correct_answer.includes(key)) html += ' \u2713';
                        html += '</div>';
                    }
                }
                
                html += '<p class="mt-2"><strong>\u4F60\u7684\u7B54\u6848\uFF1A</strong>' + (r.user_answer || '\u672A\u4F5C\u7B54') + '</p>';
                html += '<p><strong>\u6B63\u786E\u7B54\u6848\uFF1A</strong>' + r.correct_answer + '</p>';
                
                if (r.analysis) {
                    html += '<div class="analysis-box"><strong>\u89E3\u6790\uFF1A</strong>' + r.analysis + '</div>';
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
    <\/script>
</body>
</html>
`;
}
__name(getExamHTML, "getExamHTML");
function getTeacherHTML() {
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>\u6559\u5E08\u7BA1\u7406 - \u706B\u7535\u673A\u7EC4\u8003\u6838\u7CFB\u7EDF</title>
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
            <h1><i class="bi bi-person-badge-fill"></i> \u6559\u5E08\u7BA1\u7406\u540E\u53F0</h1>
        </div>
    </div>
    
    <div class="container">
        <!-- \u767B\u5F55\u9875 -->
        <div id="loginSection" class="section active">
            <div class="card">
                <div class="card-body text-center">
                    <i class="bi bi-shield-lock" style="font-size:80px;color:var(--success)"></i>
                    <h4 class="mt-3">\u6559\u5E08\u767B\u5F55</h4>
                    <div class="mt-4">
                        <input type="text" class="form-control form-control-lg" id="teacherId" placeholder="\u8BF7\u8F93\u5165\u6559\u5E08\u5DE5\u53F7">
                        <button class="btn btn-success btn-lg w-100 mt-3" onclick="teacherLogin()">
                            <i class="bi bi-box-arrow-in-right me-2"></i>\u767B\u5F55
                        </button>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> \u8FD4\u56DE\u9996\u9875</a>
        </div>
        
        <!-- \u7EDF\u8BA1\u9875 -->
        <div id="statsSection" class="section">
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-num" id="totalStudents">70</div>
                        <div class="stat-label">\u5B66\u751F\u603B\u6570</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card" style="background:linear-gradient(135deg,var(--success),#2d8a47)">
                        <div class="stat-num" id="examinedCount">0</div>
                        <div class="stat-label">\u5DF2\u8003\u8BD5\u4EBA\u6570</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card" style="background:linear-gradient(135deg,var(--warning),#d97706)">
                        <div class="stat-num" id="avgScore">0</div>
                        <div class="stat-label">\u5E73\u5747\u5206</div>
                    </div>
                </div>
            </div>
            
            <!-- \u7AE0\u8282\u51FA\u9898\u529F\u80FD -->
            <div class="card mb-4">
                <div class="card-body">
                    <h5><i class="bi bi-book-half me-2"></i>\u7AE0\u8282\u51FA\u9898</h5>
                    <p class="text-muted small mb-3">\u9009\u62E9\u7AE0\u8282\u751F\u6210\u4E13\u5C5E\u8003\u8BD5\u94FE\u63A5\uFF0C\u5B66\u751F\u901A\u8FC7\u8BE5\u94FE\u63A5\u53EA\u80FD\u8003\u6240\u9009\u7AE0\u8282\u7684\u9898\u76EE</p>
                    
                    <div class="mb-3">
                        <label class="form-label">\u9009\u62E9\u7AE0\u8282</label>
                        <select class="form-select" id="chapterSelect">
                            <option value="">-- \u5168\u9898\u5E93\uFF08\u4E0D\u9650\u5236\u7AE0\u8282\uFF09--</option>
                        </select>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateChapterLink()">
                        <i class="bi bi-link-45deg me-2"></i>\u751F\u6210\u8003\u8BD5\u94FE\u63A5
                    </button>
                    
                    <div id="linkDisplay" class="mt-3" style="display:none">
                        <div class="alert alert-info mb-0">
                            <strong>\u8003\u8BD5\u94FE\u63A5\uFF1A</strong><br>
                            <input type="text" class="form-control mt-2" id="examLink" readonly>
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="copyLink()">
                                <i class="bi bi-clipboard me-1"></i>\u590D\u5236\u94FE\u63A5
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <h5><i class="bi bi-list-ul me-2"></i>\u8003\u8BD5\u8BB0\u5F55</h5>
                    <div id="recordsList" class="mt-3 table-responsive">
                        <p class="text-muted text-center">\u6682\u65E0\u8003\u8BD5\u8BB0\u5F55</p>
                    </div>
                </div>
            </div>
            <a href="/" class="btn btn-outline-secondary mt-3"><i class="bi bi-arrow-left"></i> \u8FD4\u56DE\u9996\u9875</a>
        </div>
    </div>
    
    <script>
        async function teacherLogin() {
            const teacherId = document.getElementById('teacherId').value.trim();
            if (!teacherId) { alert('\u8BF7\u8F93\u5165\u6559\u5E08\u5DE5\u53F7'); return; }
            
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
                alert('\u767B\u5F55\u5931\u8D25\uFF1A' + e.message);
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
                        let html = '<table class="table"><thead><tr><th>\u5B66\u53F7</th><th>\u59D3\u540D</th><th>\u5206\u6570</th><th>\u7528\u65F6</th><th>\u65F6\u95F4</th></tr></thead><tbody>';
                        data.records.forEach(r => {
                            const duration = r.duration_seconds ? Math.floor(r.duration_seconds / 60) + '\u5206' : '-';
                            const time = r.end_time ? r.end_time.substring(0, 16).replace('T', ' ') : '-';
                            html += '<tr><td>' + r.student_id + '</td><td>' + (r.student_name || '-') + '</td><td>' + r.score + '</td><td>' + duration + '</td><td>' + time + '</td></tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('recordsList').innerHTML = html;
                    }
                }
            } catch (e) {
                console.error('\u52A0\u8F7D\u7EDF\u8BA1\u5931\u8D25', e);
            }
            
            // \u52A0\u8F7D\u7AE0\u8282\u5217\u8868
            loadChapters();
        }
        
        // \u52A0\u8F7D\u7AE0\u8282\u5217\u8868
        async function loadChapters() {
            try {
                const res = await fetch('/api/exam/chapters');
                const data = await res.json();
                
                if (data.success && data.chapters) {
                    const select = document.getElementById('chapterSelect');
                    data.chapters.forEach(ch => {
                        const option = document.createElement('option');
                        option.value = ch.chapter;
                        option.textContent = ch.chapter + ' (' + ch.count + '\u9898)';
                        select.appendChild(option);
                    });
                }
            } catch (e) {
                console.error('\u52A0\u8F7D\u7AE0\u8282\u5931\u8D25', e);
            }
        }
        
        // \u751F\u6210\u7AE0\u8282\u8003\u8BD5\u94FE\u63A5
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
                    alert('\u751F\u6210\u94FE\u63A5\u5931\u8D25\uFF1A' + data.message);
                }
            } catch (e) {
                alert('\u751F\u6210\u94FE\u63A5\u5931\u8D25\uFF1A' + e.message);
            }
        }
        
        // \u590D\u5236\u94FE\u63A5
        function copyLink() {
            const linkInput = document.getElementById('examLink');
            linkInput.select();
            document.execCommand('copy');
            alert('\u94FE\u63A5\u5DF2\u590D\u5236\u5230\u526A\u8D34\u677F\uFF01');
        }
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }
    <\/script>
</body>
</html>
`;
}
__name(getTeacherHTML, "getTeacherHTML");
router.options("*", () => new Response(null, { headers: corsHeaders }));
router.all("*", () => new Response("Not Found", { status: 404 }));
var worker_default = {
  async fetch(request, env, ctx) {
    return router.handle(request, env, ctx);
  }
};

// ../../../root/.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e2) {
      console.error("Failed to drain the unused request body.", e2);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../root/.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e2) {
  return {
    name: e2?.name,
    message: e2?.message ?? String(e2),
    stack: e2?.stack,
    cause: e2?.cause === void 0 ? void 0 : reduceError(e2.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e2) {
    const error = reduceError(e2);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-wgObnX/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;

// ../../../root/.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-wgObnX/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=worker.js.map
