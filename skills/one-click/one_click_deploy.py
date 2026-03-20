#!/usr/bin/env python3
"""
一键部署技能

整合所有技能，提供一键部署能力
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加技能目录到路径
SKILLS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILLS_DIR / "data-sync"))
sys.path.insert(0, str(SKILLS_DIR / "git-sync"))
sys.path.insert(0, str(SKILLS_DIR / "cloudflare-deploy"))
sys.path.insert(0, str(SKILLS_DIR / "system-check"))

WORKSPACE_ROOT = Path(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))


def sync_and_deploy(commit_message: str = "sync: 一键同步部署") -> dict:
    """
    一键同步部署
    
    流程:
    1. 检查系统状态
    2. 同步学生数据（可选）
    3. 同步题库数据（可选）
    4. Git 提交并推送
    5. 部署 Cloudflare Worker
    
    Args:
        commit_message: Git 提交消息
    
    Returns:
        执行结果
    """
    from student_sync import sync_students
    from question_sync import sync_questions
    from git_skill import sync as git_sync
    from cloudflare_skill import deploy_worker
    
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "steps": []
    }
    
    # 1. Git 同步
    git_result = git_sync(commit_message)
    results["steps"].append({
        "step": "git_sync",
        "success": git_result.get("success", False),
        "details": git_result
    })
    
    # 2. Cloudflare 部署
    success, msg, url = deploy_worker()
    results["steps"].append({
        "step": "cloudflare_deploy",
        "success": success,
        "message": msg,
        "url": url
    })
    
    if not success:
        results["success"] = False
    
    return results


def full_sync_and_deploy(
    sync_students_flag: bool = True,
    sync_questions_flag: bool = True,
    commit_message: str = "sync: 完整同步部署"
) -> dict:
    """
    完整同步部署（包含数据同步）
    
    Args:
        sync_students_flag: 是否同步学生数据
        sync_questions_flag: 是否同步题库数据
        commit_message: Git 提交消息
    
    Returns:
        执行结果
    """
    from student_sync import sync_students
    from question_sync import sync_questions
    from git_skill import sync as git_sync
    from cloudflare_skill import deploy_worker, get_d1_status
    
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "steps": [],
        "summary": {}
    }
    
    # 1. 同步学生数据
    if sync_students_flag:
        student_result = sync_students()
        results["steps"].append({
            "step": "sync_students",
            "success": student_result.get("success", False),
            "details": student_result
        })
    
    # 2. 同步题库数据
    if sync_questions_flag:
        question_result = sync_questions()
        results["steps"].append({
            "step": "sync_questions",
            "success": question_result.get("success", False),
            "details": question_result
        })
    
    # 3. Git 同步
    git_result = git_sync(commit_message)
    results["steps"].append({
        "step": "git_sync",
        "success": git_result.get("success", False),
        "details": git_result
    })
    
    # 4. Cloudflare 部署
    success, msg, url = deploy_worker()
    results["steps"].append({
        "step": "cloudflare_deploy",
        "success": success,
        "message": msg,
        "url": url
    })
    
    if not success:
        results["success"] = False
    
    # 5. 获取数据库状态
    db_status = get_d1_status()
    results["summary"]["database"] = db_status.get("tables", {})
    
    return results


def quick_deploy() -> dict:
    """
    快速部署（仅推送代码变更）
    """
    return sync_and_deploy("sync: 快速部署")


def init_deploy() -> dict:
    """
    初始化部署（首次部署，包含完整数据同步）
    """
    return full_sync_and_deploy(
        sync_students_flag=True,
        sync_questions_flag=True,
        commit_message="init: 初始化部署"
    )


def show_skills_info():
    """显示所有技能信息"""
    info = """
╔══════════════════════════════════════════════════════════════╗
║           火电机组考核系统 - 技能库                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📦 已封装技能:                                              ║
║                                                              ║
║  1. data-sync (数据同步)                                     ║
║     - student_sync: 同步学生名单到 D1                        ║
║     - question_sync: 同步题库到 D1                           ║
║                                                              ║
║  2. git-sync (Git同步)                                       ║
║     - status: 获取 Git 状态                                  ║
║     - commit: Git 提交                                       ║
║     - push: Git 推送                                         ║
║     - sync: 完整同步                                         ║
║     - quick_sync: 快速同步                                   ║
║                                                              ║
║  3. cloudflare-deploy (Cloudflare部署)                       ║
║     - deploy: 部署 Worker                                    ║
║     - query: 查询 D1 数据库                                  ║
║     - import: 导入数据到 D1                                  ║
║     - status: 获取 D1 状态                                   ║
║                                                              ║
║  4. system-check (系统检查)                                  ║
║     - files: 检查本地文件                                    ║
║     - database: 检查数据库                                   ║
║     - git: 检查 Git 状态                                     ║
║     - credentials: 检查凭证                                  ║
║     - full: 完整检查                                         ║
║     - report: 生成报告                                       ║
║                                                              ║
║  5. one-click (一键部署)                                     ║
║     - sync_and_deploy: 一键同步部署                          ║
║     - full_sync_and_deploy: 完整同步部署                     ║
║     - quick_deploy: 快速部署                                 ║
║     - init_deploy: 初始化部署                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

使用方式:
  python one_click_deploy.py <命令>

命令列表:
  sync_and_deploy    - 一键同步部署（Git + Cloudflare）
  full_sync          - 完整同步部署（包含数据同步）
  quick_deploy       - 快速部署
  init_deploy        - 初始化部署
  info               - 显示技能信息
"""
    print(info)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_skills_info()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "sync_and_deploy":
        msg = sys.argv[2] if len(sys.argv) > 2 else "sync: 一键同步部署"
        result = sync_and_deploy(msg)
    elif command == "full_sync":
        result = full_sync_and_deploy()
    elif command == "quick_deploy":
        result = quick_deploy()
    elif command == "init_deploy":
        result = init_deploy()
    elif command == "info":
        show_skills_info()
        sys.exit(0)
    else:
        result = {"error": f"未知命令: {command}"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
