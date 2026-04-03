#!/usr/bin/env python3
"""
Git 同步技能

封装 Git 提交和推送操作
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))
CREDENTIALS_FILE = WORKSPACE_ROOT / ".config" / "credentials.json"


def load_credentials() -> Dict:
    """加载凭证"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_status() -> Dict:
    """
    获取 Git 状态
    
    Returns:
        状态信息
    """
    os.chdir(WORKSPACE_ROOT)
    
    # 获取变更文件
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    # 获取当前分支
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True
    )
    branch = result.stdout.strip()
    
    # 获取最新提交
    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        capture_output=True, text=True
    )
    last_commit = result.stdout.strip()
    
    return {
        "branch": branch,
        "has_changes": len([c for c in changes if c]) > 0,
        "changes": [c for c in changes if c],
        "changes_count": len([c for c in changes if c]),
        "last_commit": last_commit
    }


def add_files(files: List[str] = None) -> Tuple[bool, str]:
    """
    添加文件到暂存区
    
    Args:
        files: 文件列表，None 表示添加所有
    
    Returns:
        (成功状态, 消息)
    """
    os.chdir(WORKSPACE_ROOT)
    
    if files is None:
        result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
    else:
        result = subprocess.run(["git", "add"] + files, capture_output=True, text=True)
    
    if result.returncode == 0:
        return True, "添加成功"
    else:
        return False, f"添加失败: {result.stderr}"


def commit(message: str) -> Tuple[bool, str]:
    """
    Git 提交
    
    Args:
        message: 提交消息
    
    Returns:
        (成功状态, 消息)
    """
    os.chdir(WORKSPACE_ROOT)
    
    # 检查是否有变更
    status = get_status()
    if not status["has_changes"]:
        return True, "没有需要提交的变更"
    
    # 添加所有变更
    add_files()
    
    # 提交
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, f"提交成功: {message}"
    else:
        return False, f"提交失败: {result.stderr}"


def push(branch: str = "main") -> Tuple[bool, str]:
    """
    Git 推送
    
    Args:
        branch: 分支名称
    
    Returns:
        (成功状态, 消息)
    """
    os.chdir(WORKSPACE_ROOT)
    
    creds = load_credentials()
    token = creds.get("github", {}).get("token", "")
    
    # 设置远程 URL（带 token）
    if token:
        repo_url = f"https://{token}@github.com/user03413/hd-exam-system.git"
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], capture_output=True)
    
    # 推送
    result = subprocess.run(
        ["git", "push", "origin", branch],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, "推送成功"
    else:
        return False, f"推送失败: {result.stderr}"


def pull(branch: str = "main") -> Tuple[bool, str]:
    """
    Git 拉取
    
    Args:
        branch: 分支名称
    
    Returns:
        (成功状态, 消息)
    """
    os.chdir(WORKSPACE_ROOT)
    
    result = subprocess.run(
        ["git", "pull", "origin", branch],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, "拉取成功"
    else:
        return False, f"拉取失败: {result.stderr}"


def sync(commit_message: str = "sync: 自动同步") -> Dict:
    """
    完整同步流程（提交 + 推送）
    
    Args:
        commit_message: 提交消息
    
    Returns:
        执行结果
    """
    results = {
        "success": True,
        "steps": [],
        "status": {}
    }
    
    # 1. 获取状态
    results["status"] = get_status()
    
    # 2. 提交
    success, msg = commit(commit_message)
    results["steps"].append({"step": "commit", "success": success, "message": msg})
    
    # 3. 推送
    success, msg = push()
    results["steps"].append({"step": "push", "success": success, "message": msg})
    
    if not success:
        results["success"] = False
    
    return results


def quick_sync(message_type: str = "sync") -> Dict:
    """
    快速同步（使用预设消息模板）
    
    Args:
        message_type: 消息类型 (sync/feat/fix/docs/chore)
    
    Returns:
        执行结果
    """
    messages = {
        "sync": "sync: 自动同步",
        "feat": "feat: 新功能",
        "fix": "fix: 修复问题",
        "docs": "docs: 文档更新",
        "chore": "chore: 其他更新"
    }
    
    commit_message = messages.get(message_type, f"{message_type}: 更新")
    return sync(commit_message)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python git_skill.py <命令> [参数]")
        print("命令: status, commit, push, pull, sync, quick_sync")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        result = get_status()
    elif command == "commit" and len(sys.argv) > 2:
        result = commit(sys.argv[2])
    elif command == "push":
        result = push()
    elif command == "pull":
        result = pull()
    elif command == "sync" and len(sys.argv) > 2:
        result = sync(sys.argv[2])
    elif command == "quick_sync" and len(sys.argv) > 2:
        result = quick_sync(sys.argv[2])
    else:
        result = {"error": "无效命令或参数不足"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
