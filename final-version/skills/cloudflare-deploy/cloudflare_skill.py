#!/usr/bin/env python3
"""
Cloudflare 部署技能

封装 Cloudflare Workers 和 D1 数据库的部署操作
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"
CLOUDFLARE_WORKER_DIR = WORKSPACE_ROOT / "cloudflare-worker"


def load_credentials() -> Dict:
    """加载凭证"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_worker_info() -> Dict:
    """
    获取 Worker 信息
    
    Returns:
        Worker 配置信息
    """
    wrangler_path = CLOUDFLARE_WORKER_DIR / "wrangler.toml"
    
    if not wrangler_path.exists():
        return {"error": "wrangler.toml 不存在"}
    
    with open(wrangler_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析基本信息
    info = {
        "worker_name": "hd-exam-api",
        "worker_url": "https://hd-exam-api.771794850.workers.dev",
        "d1_database": "hd-exam-db"
    }
    
    return info


def deploy_worker() -> Tuple[bool, str, Optional[str]]:
    """
    部署 Cloudflare Worker
    
    Returns:
        (成功状态, 消息, 部署URL)
    """
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = load_credentials()
    api_token = creds.get("cloudflare", {}).get("api_token", "")
    
    env = os.environ.copy()
    if api_token:
        env["CLOUDFLARE_API_TOKEN"] = api_token
    
    result = subprocess.run(
        ["npx", "wrangler", "deploy"],
        capture_output=True, text=True, env=env
    )
    
    if result.returncode == 0:
        # 提取部署 URL
        url = "https://hd-exam-api.771794850.workers.dev"
        for line in result.stdout.split('\n'):
            if 'workers.dev' in line and 'https' in line:
                url = line.strip()
                break
        
        # 提取版本 ID
        version_id = ""
        for line in result.stdout.split('\n'):
            if 'Current Version ID' in line or 'Version ID' in line:
                version_id = line.split(':')[-1].strip()
                break
        
        return True, f"部署成功", url
    
    else:
        return False, f"部署失败: {result.stderr}", None


def execute_d1_sql(sql: str, is_file: bool = False) -> Tuple[bool, str, Optional[list]]:
    """
    执行 D1 SQL
    
    Args:
        sql: SQL 语句或文件路径
        is_file: 是否为文件路径
    
    Returns:
        (成功状态, 消息, 结果列表)
    """
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = load_credentials()
    api_token = creds.get("cloudflare", {}).get("api_token", "")
    
    env = os.environ.copy()
    if api_token:
        env["CLOUDFLARE_API_TOKEN"] = api_token
    
    cmd = ["npx", "wrangler", "d1", "execute", "hd-exam-db", "--remote"]
    
    if is_file:
        cmd.extend(["--file", sql])
    else:
        cmd.extend(["--command", sql])
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        # 尝试解析 JSON 结果
        try:
            # 提取 JSON 部分
            stdout = result.stdout
            if '[{' in stdout:
                json_start = stdout.index('[{')
                json_end = stdout.rindex('}]') + 2
                json_str = stdout[json_start:json_end]
                results = json.loads(json_str)
                return True, "执行成功", results
        except:
            pass
        
        return True, "执行成功", None
    
    else:
        return False, f"执行失败: {result.stderr}", None


def query_d1(sql: str) -> Tuple[bool, str, Optional[list]]:
    """
    查询 D1 数据库
    
    Args:
        sql: SELECT 查询语句
    
    Returns:
        (成功状态, 消息, 查询结果)
    """
    return execute_d1_sql(sql, is_file=False)


def import_d1_data(sql_file: str) -> Tuple[bool, str]:
    """
    导入数据到 D1 数据库
    
    Args:
        sql_file: SQL 文件路径
    
    Returns:
        (成功状态, 消息)
    """
    success, msg, _ = execute_d1_sql(sql_file, is_file=True)
    return success, msg


def get_d1_status() -> Dict:
    """
    获取 D1 数据库状态
    
    Returns:
        数据库状态信息
    """
    results = {
        "success": True,
        "tables": {}
    }
    
    # 查询各表记录数
    tables = ["students", "questions", "exam_records"]
    
    for table in tables:
        success, msg, result = query_d1(f"SELECT COUNT(*) as count FROM {table}")
        if success and result:
            try:
                count = result[0].get("results", [{}])[0].get("count", 0)
                results["tables"][table] = {"count": count}
            except:
                results["tables"][table] = {"count": 0, "error": "解析失败"}
        else:
            results["tables"][table] = {"error": msg}
    
    return results


def deploy_full() -> Dict:
    """
    完整部署流程（Worker + 数据库检查）
    
    Returns:
        执行结果
    """
    results = {
        "success": True,
        "steps": [],
        "info": {}
    }
    
    # 1. 获取配置信息
    results["info"] = get_worker_info()
    
    # 2. 部署 Worker
    success, msg, url = deploy_worker()
    results["steps"].append({
        "step": "deploy_worker",
        "success": success,
        "message": msg,
        "url": url
    })
    
    if not success:
        results["success"] = False
        return results
    
    # 3. 检查数据库状态
    status = get_d1_status()
    results["steps"].append({
        "step": "check_database",
        "success": True,
        "tables": status["tables"]
    })
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python cloudflare_skill.py <命令> [参数]")
        print("命令: info, deploy, query, import, status, deploy_full")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "info":
        result = get_worker_info()
    elif command == "deploy":
        success, msg, url = deploy_worker()
        result = {"success": success, "message": msg, "url": url}
    elif command == "query" and len(sys.argv) > 2:
        success, msg, data = query_d1(sys.argv[2])
        result = {"success": success, "message": msg, "data": data}
    elif command == "import" and len(sys.argv) > 2:
        success, msg = import_d1_data(sys.argv[2])
        result = {"success": success, "message": msg}
    elif command == "status":
        result = get_d1_status()
    elif command == "deploy_full":
        result = deploy_full()
    else:
        result = {"error": "无效命令或参数不足"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
