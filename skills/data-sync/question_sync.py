#!/usr/bin/env python3
"""
数据同步技能 - 题库同步

从 Excel 文件读取题库数据并同步到 Cloudflare D1 数据库
"""

import os
import json
import subprocess
import pandas as pd
import re
from pathlib import Path
from typing import Dict, Tuple

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"
CLOUDFLARE_WORKER_DIR = WORKSPACE_ROOT / "cloudflare-worker"


def load_credentials() -> Dict:
    """加载凭证"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def parse_options(option_str: str) -> Dict:
    """解析选项字符串为字典"""
    options = {}
    if pd.isna(option_str) or not option_str:
        return options
    
    pattern = r'([A-F])\.\s*([^A-F]+?)(?=\s*[A-F]\.|$)'
    matches = re.findall(pattern, str(option_str) + ' ')
    
    for letter, content in matches:
        options[letter.strip()] = content.strip()
    
    return options


def generate_questions_sql(excel_path: str, sheet_name: str = None, output_path: str = None) -> Tuple[bool, str, int]:
    """
    从 Excel 生成题库 SQL
    
    Args:
        excel_path: Excel 文件路径
        sheet_name: 工作表名称
        output_path: SQL 输出路径
    
    Returns:
        (成功状态, 消息, 题目数量)
    """
    try:
        if sheet_name:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(excel_path)
        
        if output_path is None:
            output_path = CLOUDFLARE_WORKER_DIR / "questions_sync.sql"
        else:
            output_path = Path(output_path)
        
        sql_lines = ["""-- 题库表
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,
  question TEXT NOT NULL,
  options TEXT,
  answer TEXT NOT NULL,
  analysis TEXT,
  chapter TEXT,
  page TEXT,
  difficulty TEXT DEFAULT '中等'
);
"""]
        
        for _, row in df.iterrows():
            q_type = str(row['题型']).strip().replace("'", "''")
            question = str(row['题目']).strip().replace("'", "''")
            
            options = parse_options(row.get('选项', ''))
            options_json = json.dumps(options, ensure_ascii=False).replace("'", "''")
            
            answer = str(row['答案']).strip().replace("'", "''")
            analysis = str(row['解析']).strip().replace("'", "''") if pd.notna(row.get('解析', '')) else ''
            chapter = str(row.get('教材章节', '')).strip().replace("'", "''")
            page = str(row.get('页码', '')).strip().replace("'", "''") if pd.notna(row.get('页码', '')) else ''
            
            # 处理难度
            difficulty = '中等'
            if pd.notna(row.get('难度', '')):
                diff_text = re.sub(r'<[^>]+>', '', str(row['难度']))
                difficulty = diff_text.strip() if diff_text.strip() else '中等'
            
            sql_lines.append(
                f"INSERT INTO questions (type, question, options, answer, analysis, chapter, page, difficulty) "
                f"VALUES ('{q_type}', '{question}', '{options_json}', '{answer}', '{analysis}', '{chapter}', '{page}', '{difficulty}');"
            )
        
        sql_lines.append("\nCREATE INDEX IF NOT EXISTS idx_question_type ON questions(type);")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
        
        return True, f"生成成功: {output_path}", len(df)
    
    except Exception as e:
        return False, f"生成失败: {str(e)}", 0


def sync_to_d1(sql_file: str) -> Tuple[bool, str]:
    """同步 SQL 到 D1 数据库"""
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = load_credentials()
    api_token = creds.get("cloudflare", {}).get("api_token", "")
    
    env = os.environ.copy()
    if api_token:
        env["CLOUDFLARE_API_TOKEN"] = api_token
    
    result = subprocess.run(
        ["npx", "wrangler", "d1", "execute", "hd-exam-db", "--remote", "--file", sql_file],
        capture_output=True, text=True, env=env
    )
    
    if result.returncode == 0:
        return True, "同步成功"
    else:
        return False, f"同步失败: {result.stderr}"


def sync_questions(excel_path: str = None, sheet_name: str = None) -> Dict:
    """
    完整的题库同步流程
    
    Args:
        excel_path: Excel 文件路径
        sheet_name: 工作表名称
    
    Returns:
        执行结果
    """
    if excel_path is None:
        excel_path = WORKSPACE_ROOT / "assets" / "244题_热工自动化试题集.xlsx"
    
    results = {
        "success": True,
        "steps": [],
        "total_questions": 0
    }
    
    # 1. 生成 SQL
    success, msg, count = generate_questions_sql(str(excel_path), sheet_name)
    results["steps"].append({"step": "generate_sql", "success": success, "message": msg})
    results["total_questions"] = count
    
    if not success:
        results["success"] = False
        return results
    
    # 2. 同步到 D1
    sql_file = CLOUDFLARE_WORKER_DIR / "questions_sync.sql"
    success, msg = sync_to_d1(str(sql_file))
    results["steps"].append({"step": "sync_to_d1", "success": success, "message": msg})
    
    if not success:
        results["success"] = False
    
    return results


if __name__ == "__main__":
    import sys
    excel_path = sys.argv[1] if len(sys.argv) > 1 else None
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    result = sync_questions(excel_path, sheet_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
