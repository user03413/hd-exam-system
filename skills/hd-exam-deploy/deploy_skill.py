#!/usr/bin/env python3
"""
火电机组考核系统 - 部署工具 Skill

封装 GitHub 和 Cloudflare 的部署操作，支持命令：
- 同步部署：GitHub + Cloudflare
- 同步：仅 GitHub
- 部署：仅 Cloudflare
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ==================== 配置 ====================

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"
CLOUDFLARE_WORKER_DIR = WORKSPACE_ROOT / "cloudflare-worker"

# 凭证（从文件或环境变量加载）
_credentials = None

def _load_credentials() -> Dict:
    """加载凭证"""
    global _credentials
    if _credentials:
        return _credentials
    
    # 尝试从文件加载
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            _credentials = json.load(f)
            return _credentials
    
    # 从环境变量加载
    _credentials = {
        "github": {
            "username": os.getenv("GITHUB_USERNAME", "user03413"),
            "token": os.getenv("GITHUB_TOKEN", ""),
            "repo": os.getenv("GITHUB_REPO", "https://github.com/user03413/hd-exam-system.git")
        },
        "cloudflare": {
            "account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID", "57d6cde2e053b14fd28bd963ddb0975b"),
            "api_token": os.getenv("CLOUDFLARE_API_TOKEN", "")
        }
    }
    return _credentials


# ==================== GitHub 操作 ====================

def git_status() -> Dict:
    """获取 Git 状态"""
    os.chdir(WORKSPACE_ROOT)
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return {
        "has_changes": len(changes) > 0,
        "changes": changes,
        "count": len(changes)
    }


def git_commit(message: str = "sync: 自动同步") -> Tuple[bool, str]:
    """Git 提交"""
    os.chdir(WORKSPACE_ROOT)
    
    # 检查是否有变更
    status = git_status()
    if not status["has_changes"]:
        return True, "没有需要提交的变更"
    
    # 添加所有变更
    subprocess.run(["git", "add", "-A"], capture_output=True)
    
    # 提交
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, f"提交成功: {message}"
    else:
        return False, f"提交失败: {result.stderr}"


def git_push() -> Tuple[bool, str]:
    """Git 推送到 GitHub"""
    os.chdir(WORKSPACE_ROOT)
    
    creds = _load_credentials()
    token = creds["github"].get("token", "")
    
    # 设置远程 URL（带 token）
    if token:
        repo_url = f"https://{token}@github.com/user03413/hd-exam-system.git"
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], capture_output=True)
    
    # 推送
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, "推送成功"
    else:
        return False, f"推送失败: {result.stderr}"


def sync_to_github(commit_message: str = "sync: 自动同步") -> Dict:
    """同步到 GitHub（提交 + 推送）"""
    results = {
        "success": True,
        "steps": []
    }
    
    # 提交
    success, msg = git_commit(commit_message)
    results["steps"].append({"step": "commit", "success": success, "message": msg})
    if not success and "没有需要提交" not in msg:
        results["success"] = False
        return results
    
    # 推送
    success, msg = git_push()
    results["steps"].append({"step": "push", "success": success, "message": msg})
    if not success:
        results["success"] = False
    
    return results


# ==================== Cloudflare 操作 ====================

def deploy_cloudflare_worker() -> Tuple[bool, str]:
    """部署 Cloudflare Worker"""
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = _load_credentials()
    api_token = creds["cloudflare"].get("api_token", "")
    
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
            if 'workers.dev' in line:
                url = line.strip()
                break
        return True, f"部署成功: {url}"
    else:
        return False, f"部署失败: {result.stderr}"


def execute_d1_sql(sql: str, file: bool = False) -> Tuple[bool, str]:
    """执行 D1 SQL"""
    os.chdir(CLOUDFLARE_WORKER_DIR)
    
    creds = _load_credentials()
    api_token = creds["cloudflare"].get("api_token", "")
    
    env = os.environ.copy()
    if api_token:
        env["CLOUDFLARE_API_TOKEN"] = api_token
    
    cmd = ["npx", "wrangler", "d1", "execute", "hd-exam-db", "--remote"]
    if file:
        cmd.extend(["--file", sql])
    else:
        cmd.extend(["--command", sql])
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        return True, result.stdout
    else:
        return False, result.stderr


def deploy_to_cloudflare() -> Dict:
    """部署到 Cloudflare"""
    results = {
        "success": True,
        "steps": []
    }
    
    # 部署 Worker
    success, msg = deploy_cloudflare_worker()
    results["steps"].append({"step": "deploy_worker", "success": success, "message": msg})
    
    if not success:
        results["success"] = False
    
    return results


# ==================== 组合命令 ====================

def sync_and_deploy(commit_message: str = "sync: 同步部署") -> Dict:
    """同步部署：GitHub + Cloudflare"""
    results = {
        "success": True,
        "platforms": {}
    }
    
    # GitHub 同步
    github_result = sync_to_github(commit_message)
    results["platforms"]["github"] = github_result
    if not github_result["success"]:
        results["success"] = False
    
    # Cloudflare 部署
    cf_result = deploy_to_cloudflare()
    results["platforms"]["cloudflare"] = cf_result
    if not cf_result["success"]:
        results["success"] = False
    
    return results


# ==================== 命令入口 ====================

def execute_command(command: str, commit_message: str = "sync: 自动同步") -> Dict:
    """
    执行部署命令
    
    Args:
        command: 命令名称（同步部署/同步/部署）
        commit_message: Git 提交消息
    
    Returns:
        执行结果
    """
    command = command.strip()
    
    if command == "同步部署":
        return sync_and_deploy(commit_message)
    elif command == "同步":
        return {"platforms": {"github": sync_to_github(commit_message)}}
    elif command == "部署":
        return {"platforms": {"cloudflare": deploy_to_cloudflare()}}
    else:
        return {
            "success": False,
            "error": f"未知命令: {command}。支持的命令：同步部署、同步、部署"
        }


# ==================== 工具函数 ====================

def get_worker_url() -> str:
    """获取 Worker URL"""
    return "https://hd-exam-api.771794850.workers.dev"

def get_github_url() -> str:
    """获取 GitHub 仓库 URL"""
    return "https://github.com/user03413/hd-exam-system"

def get_deploy_info() -> Dict:
    """获取部署信息"""
    return {
        "github": {
            "url": get_github_url(),
            "status": "已配置"
        },
        "cloudflare": {
            "worker_url": get_worker_url(),
            "d1_database": "hd-exam-db",
            "status": "已配置"
        },
        "credentials_loaded": bool(_load_credentials().get("github", {}).get("token"))
    }


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python deploy_skill.py <命令>")
        print("支持的命令: 同步部署、同步、部署")
        sys.exit(1)
    
    command = sys.argv[1]
    result = execute_command(command)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
