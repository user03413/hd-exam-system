#!/usr/bin/env python3
"""
数据同步技能 - 学生名单同步

从 Excel 文件读取学生数据并同步到 Cloudflare D1 数据库
"""

import os
import json
import subprocess
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"
CLOUDFLARE_WORKER_DIR = WORKSPACE_ROOT / "cloudflare-worker"


def load_credentials() -> Dict:
    """加载凭证"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def generate_students_sql(excel_path: str, output_path: str = None) -> Tuple[bool, str, int]:
    """
    从 Excel 生成学生数据 SQL
    
    Args:
        excel_path: Excel 文件路径
        output_path: SQL 输出路径（可选）
    
    Returns:
        (成功状态, 消息, 学生数量)
    """
    try:
        df = pd.read_excel(excel_path)
        
        if output_path is None:
            output_path = CLOUDFLARE_WORKER_DIR / "students_sync.sql"
        else:
            output_path = Path(output_path)
        
        sql_lines = ["-- 学生名单同步 SQL"]
        
        for _, row in df.iterrows():
            student_id = str(int(row['学号'])).strip() if pd.notna(row['学号']) else ''
            if not student_id:
                continue
            
            name = str(row['姓名']).strip().replace("'", "''") if pd.notna(row['姓名']) else ''
            major = str(row.get('专业', '控制工程')).strip().replace("'", "''")
            
            sql_lines.append(
                f"INSERT OR REPLACE INTO students (id, name, major, is_teacher) "
                f"VALUES ('{student_id}', '{name}', '{major}', 0);"
            )
        
        # 添加默认账号
        sql_lines.extend([
            "-- 测试账号",
            "INSERT OR REPLACE INTO students (id, name, major, is_teacher) VALUES ('123456', '测试学生', '控制工程（测试）', 0);",
            "INSERT OR REPLACE INTO students (id, name, major, is_teacher) VALUES ('654321', '教师管理员', '教师', 1);"
        ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
        
        return True, f"生成成功: {output_path}", len(df)
    
    except Exception as e:
        return False, f"生成失败: {str(e)}", 0


def sync_to_d1(sql_file: str) -> Tuple[bool, str]:
    """
    同步 SQL 到 D1 数据库
    
    Args:
        sql_file: SQL 文件路径
    
    Returns:
        (成功状态, 消息)
    """
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


def sync_students(excel_path: str = None) -> Dict:
    """
    完整的学生数据同步流程
    
    Args:
        excel_path: Excel 文件路径（默认使用 assets/火电机组考核学生名单.xlsx）
    
    Returns:
        执行结果
    """
    if excel_path is None:
        excel_path = WORKSPACE_ROOT / "assets" / "火电机组考核学生名单.xlsx"
    
    results = {
        "success": True,
        "steps": [],
        "total_students": 0
    }
    
    # 1. 生成 SQL
    success, msg, count = generate_students_sql(str(excel_path))
    results["steps"].append({"step": "generate_sql", "success": success, "message": msg})
    results["total_students"] = count
    
    if not success:
        results["success"] = False
        return results
    
    # 2. 同步到 D1
    sql_file = CLOUDFLARE_WORKER_DIR / "students_sync.sql"
    success, msg = sync_to_d1(str(sql_file))
    results["steps"].append({"step": "sync_to_d1", "success": success, "message": msg})
    
    if not success:
        results["success"] = False
    
    return results


if __name__ == "__main__":
    import sys
    excel_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = sync_students(excel_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
