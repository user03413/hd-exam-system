#!/usr/bin/env python3
"""
系统检查技能

检查火电机组考核系统的运行状态
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"
CLOUDFLARE_WORKER_DIR = WORKSPACE_ROOT / "cloudflare-worker"


def load_credentials() -> Dict:
    """加载凭证"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def check_local_files() -> Dict:
    """
    检查本地文件
    
    Returns:
        文件检查结果
    """
    required_files = {
        "学生名单": "assets/火电机组考核学生名单.xlsx",
        "题库文件": "assets/244题_热工自动化试题集.xlsx",
        "Worker代码": "cloudflare-worker/src/worker.js",
        "wrangler配置": "cloudflare-worker/wrangler.toml",
        "后端代码": "src/exam_routes_new.py",
        "主入口": "src/main.py"
    }
    
    results = {}
    
    for name, path in required_files.items():
        full_path = WORKSPACE_ROOT / path
        if full_path.exists():
            stat = full_path.stat()
            results[name] = {
                "exists": True,
                "size": f"{stat.st_size / 1024:.1f} KB",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            results[name] = {"exists": False}
    
    return results


def check_database() -> Dict:
    """
    检查 D1 数据库
    
    Returns:
        数据库检查结果
    """
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = load_credentials()
    api_token = creds.get("cloudflare", {}).get("api_token", "")
    
    env = os.environ.copy()
    if api_token:
        env["CLOUDFLARE_API_TOKEN"] = api_token
    
    results = {
        "connected": False,
        "tables": {}
    }
    
    # 查询各表
    tables = ["students", "questions", "exam_records"]
    
    for table in tables:
        result = subprocess.run(
            ["npx", "wrangler", "d1", "execute", "hd-exam-db", "--remote", "--command", 
             f"SELECT COUNT(*) as count FROM {table}"],
            capture_output=True, text=True, env=env
        )
        
        if result.returncode == 0:
            try:
                # 解析结果
                if '[{' in result.stdout:
                    json_start = result.stdout.index('[{')
                    json_end = result.stdout.rindex('}]') + 2
                    json_str = result.stdout[json_start:json_end]
                    data = json.loads(json_str)
                    count = data[0].get("results", [{}])[0].get("count", 0)
                    results["tables"][table] = {"count": count}
                    results["connected"] = True
            except:
                results["tables"][table] = {"error": "解析失败"}
        else:
            results["tables"][table] = {"error": "查询失败"}
    
    return results


def check_git_status() -> Dict:
    """
    检查 Git 状态
    
    Returns:
        Git 状态
    """
    os.chdir(WORKSPACE_ROOT)
    
    results = {}
    
    # 当前分支
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True
    )
    results["branch"] = result.stdout.strip()
    
    # 变更状态
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
    results["has_changes"] = len([c for c in changes if c]) > 0
    results["changes_count"] = len([c for c in changes if c])
    
    # 最新提交
    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        capture_output=True, text=True
    )
    results["last_commit"] = result.stdout.strip()
    
    # 远程状态
    result = subprocess.run(
        ["git", "remote", "-v"],
        capture_output=True, text=True
    )
    results["remote"] = "已配置" if "github.com" in result.stdout else "未配置"
    
    return results


def check_credentials() -> Dict:
    """
    检查凭证配置
    
    Returns:
        凭证状态
    """
    creds = load_credentials()
    
    results = {
        "github": {
            "configured": bool(creds.get("github", {}).get("token")),
            "username": creds.get("github", {}).get("username", "未配置")
        },
        "cloudflare": {
            "configured": bool(creds.get("cloudflare", {}).get("api_token")),
            "account_id": creds.get("cloudflare", {}).get("account_id", "未配置")[:8] + "..."
        }
    }
    
    return results


def full_check() -> Dict:
    """
    完整系统检查
    
    Returns:
        检查结果
    """
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "checks": {}
    }
    
    # 1. 本地文件
    results["checks"]["local_files"] = check_local_files()
    
    # 2. 数据库
    results["checks"]["database"] = check_database()
    
    # 3. Git 状态
    results["checks"]["git"] = check_git_status()
    
    # 4. 凭证
    results["checks"]["credentials"] = check_credentials()
    
    # 汇总状态
    files_ok = all(f.get("exists", False) for f in results["checks"]["local_files"].values())
    db_ok = results["checks"]["database"].get("connected", False)
    creds_ok = (
        results["checks"]["credentials"]["github"]["configured"] and
        results["checks"]["credentials"]["cloudflare"]["configured"]
    )
    
    results["summary"] = {
        "files_ok": files_ok,
        "database_ok": db_ok,
        "credentials_ok": creds_ok,
        "all_ok": files_ok and db_ok and creds_ok
    }
    
    if not results["summary"]["all_ok"]:
        results["success"] = False
    
    return results


def generate_report() -> str:
    """
    生成检查报告
    
    Returns:
        Markdown 格式报告
    """
    check_result = full_check()
    
    report = f"""# 火电机组考核系统 - 状态检查报告

检查时间: {check_result["timestamp"]}

## 检查结果汇总

| 检查项 | 状态 |
|--------|------|
| 本地文件 | {'✅ 正常' if check_result['summary']['files_ok'] else '❌ 异常'} |
| 数据库连接 | {'✅ 正常' if check_result['summary']['database_ok'] else '❌ 异常'} |
| 凭证配置 | {'✅ 正常' if check_result['summary']['credentials_ok'] else '❌ 异常'} |

## 数据库状态

"""
    
    for table, info in check_result["checks"]["database"].get("tables", {}).items():
        count = info.get("count", "未知")
        report += f"- **{table}**: {count} 条记录\n"
    
    report += f"""
## Git 状态

- 分支: {check_result["checks"]["git"]["branch"]}
- 未提交变更: {check_result["checks"]["git"]["changes_count"]} 个
- 最新提交: {check_result["checks"]["git"]["last_commit"]}

## 访问地址

- **统一入口**: https://90c19216-7224-4e07-9c9b-2d1be18d1149.dev.coze.site/
- **Cloudflare**: https://hd-exam-api.771794850.workers.dev/
- **GitHub**: https://github.com/user03413/hd-exam-system

---
*报告生成时间: {check_result["timestamp"]}*
"""
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python system_check.py <命令>")
        print("命令: files, database, git, credentials, full, report")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "files":
        result = check_local_files()
    elif command == "database":
        result = check_database()
    elif command == "git":
        result = check_git_status()
    elif command == "credentials":
        result = check_credentials()
    elif command == "full":
        result = full_check()
    elif command == "report":
        result = generate_report()
        print(result)
        sys.exit(0)
    else:
        result = {"error": "无效命令"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
