# 火电机组考核学习报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | {{student_name}} |
| 学号 | {{student_id}} |
| 专业 | {{major}} |
| 开始时间 | {{start_time}} |
| 结束时间 | {{end_time}} |
| 考试用时 | {{duration}} |
| 总分 | **{{total_score}}** / 100 分 |

## 成绩分析

### 题型得分

| 题型 | 题数 | 正确 | 得分 |
|------|------|------|------|
| 单选题 | 4 | {{single_correct}} | {{single_score}} |
| 多选题 | 3 | {{multiple_correct}} | {{multiple_score}} |
| 简答题 | 3 | {{short_correct}} | {{short_score}} |

### 成绩等级

**{{grade_level}}** - {{grade_comment}}

---

## 答题详情

{{#each results}}
### 题目 {{seq}}：{{type}}（{{difficulty}}）

**章节**：{{chapter}} {{chapter_title}}（第{{page}}页）

**题目**：{{question}}

{{#if options}}
**选项**：

{{#each options}}
- **{{@key}}**. {{this}}
{{/each}}
{{/if}}

**你的答案**：{{user_answer}}

**正确答案**：{{correct_answer}}

**得分**：{{score}} / 10 分 （{{#if is_correct}}正确{{else}}错误{{/if}}）

**解析**：

{{analysis}}

{{#if extension}}
{{extension}}
{{/if}}

---

{{/each}}

## 学习建议

根据本次考核表现，建议重点复习以下内容：

{{#if wrong_questions}}
{{#each wrong_questions}}
- {{chapter}} {{chapter_title}}：{{question}}
{{/each}}
{{else}}
- 恭喜！全部答对，继续保持！
{{/if}}

---

*本报告由火电机组考核系统自动生成*

*生成时间：{{generated_time}}*
