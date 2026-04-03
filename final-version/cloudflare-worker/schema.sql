-- 学生表
CREATE TABLE IF NOT EXISTS students (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  major TEXT,
  is_teacher INTEGER DEFAULT 0
);

-- 考试记录表
CREATE TABLE IF NOT EXISTS exam_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL,
  student_name TEXT,
  major TEXT,
  score INTEGER,
  duration_seconds INTEGER,
  start_time TEXT,
  end_time TEXT,
  results TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_student_id ON students(id);
CREATE INDEX IF NOT EXISTS idx_exam_student_id ON exam_records(student_id);
