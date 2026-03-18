"""同步题库到GitHub仓库"""
import os
import subprocess
from datetime import datetime
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context

# GitHub配置 - 请替换为您的GitHub用户名
GITHUB_TOKEN = "096c68c5d22d5bb20fd31a1967a70277"
GITHUB_USERNAME = "YOUR_GITHUB_USERNAME"  # 请替换为您的GitHub用户名
REPO_NAME = "hd-exam-system"


@tool
def sync_to_github(runtime: ToolRuntime = None) -> str:
    """
    同步题库到GitHub仓库。
    当用户发送'同步题库'时调用此工具，将src文件夹内容推送到main分支。
    
    Returns:
        str: 同步结果信息
    """
    ctx = runtime.context if runtime else new_context(method="sync_to_github")
    
    try:
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        today = datetime.now().strftime("%Y-%m-%d")
        commit_msg = f"更新题库 {today}"
        
        # 构建仓库URL
        repo_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
        
        # 检查git是否已初始化
        git_dir = os.path.join(workspace_path, ".git")
        
        if not os.path.exists(git_dir):
            # 初始化git仓库
            subprocess.run(["git", "init"], cwd=workspace_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "exam-system@local"], cwd=workspace_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Exam System"], cwd=workspace_path, check=True, capture_output=True)
        
        # 配置远程仓库
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        if "origin" not in result.stdout:
            subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
        else:
            subprocess.run(
                ["git", "remote", "set-url", "origin", repo_url],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
        
        # 添加要同步的文件
        files_to_add = []
        for folder in ["src", "assets", "config"]:
            folder_path = os.path.join(workspace_path, folder)
            if os.path.exists(folder_path):
                files_to_add.append(folder)
        
        for folder in files_to_add:
            subprocess.run(["git", "add", folder + "/"], cwd=workspace_path, check=True, capture_output=True)
        
        # 检查是否有变更
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return "✅ 没有需要同步的变更，题库已是最新状态。"
        
        # 提交变更
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=workspace_path,
            check=True,
            capture_output=True
        )
        
        # 获取当前分支名
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip() or "main"
        
        # 尝试推送到当前分支
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", current_branch, "--force"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            # 尝试main分支
            push_result = subprocess.run(
                ["git", "push", "-u", "origin", "main", "--force"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
        
        if push_result.returncode != 0:
            # 尝试master分支
            push_result = subprocess.run(
                ["git", "push", "-u", "origin", "master", "--force"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
        
        if push_result.returncode == 0:
            return f"""✅ 同步成功！

📝 提交信息: {commit_msg}
📂 已同步目录: {', '.join(files_to_add)}
🌐 分支: {current_branch}

🔗 仓库地址: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}"""
        else:
            error_msg = push_result.stderr or push_result.stdout
            return f"❌ 推送失败: {error_msg}"
            
    except subprocess.CalledProcessError as e:
        return f"❌ Git操作失败: {e.stderr if hasattr(e, 'stderr') else str(e)}"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"
