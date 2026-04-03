#!/usr/bin/env python3
"""
多平台静态网站部署脚本
支持: Cloudflare Pages, Vercel, GitHub Pages, Surge.sh
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"

PROJECT_NAME = "hd-exam-system"

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def log(msg: str, level: str = "INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = {"INFO": Colors.GREEN, "WARN": Colors.YELLOW, "ERROR": Colors.RED}.get(level, "")
    print(f"{color}[{timestamp}] {msg}{Colors.RESET}")

def run_cmd(cmd: list, timeout: int = 120, cwd: str = None) -> Tuple[int, str, str]:
    """运行命令"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=cwd or str(PROJECT_ROOT)
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)

def prepare_dist() -> bool:
    """准备部署目录"""
    log("准备部署文件...")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    
    # 复制离线版HTML
    offline_html = ASSETS_DIR / "火电机组考核系统_离线版.html"
    if not offline_html.exists():
        log(f"离线版HTML不存在: {offline_html}", "ERROR")
        return False
    
    shutil.copy(offline_html, DIST_DIR / "index.html")
    
    # 复制资源文件
    for item in ASSETS_DIR.iterdir():
        if item.is_file():
            shutil.copy(item, DIST_DIR / item.name)
    
    # 创建路由配置
    with open(DIST_DIR / "_redirects", "w") as f:
        f.write("/* /index.html 200\n")
    
    log(f"✓ 部署目录: {len(list(DIST_DIR.iterdir()))} 个文件")
    return True

def deploy_cloudflare() -> Optional[str]:
    """部署到 Cloudflare Pages"""
    log("尝试部署到 Cloudflare Pages...")
    
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    
    if not api_token or not account_id:
        log("未配置 CLOUDFLARE_API_TOKEN 或 CLOUDFLARE_ACCOUNT_ID", "WARN")
        return None
    
    try:
        code, out, err = run_cmd([
            "wrangler", "pages", "deploy", str(DIST_DIR),
            "--project-name", PROJECT_NAME
        ], timeout=300)
        
        output = out + err
        if code == 0 or "Deployed" in output:
            import re
            urls = re.findall(r'https://[^\s]+\.pages\.dev', output)
            return urls[0] if urls else f"https://{PROJECT_NAME}.pages.dev"
    except Exception as e:
        log(f"Cloudflare 部署失败: {e}", "WARN")
    
    return None

def deploy_vercel() -> Optional[str]:
    """部署到 Vercel"""
    log("尝试部署到 Vercel...")
    
    token = os.environ.get("VERCEL_TOKEN")
    
    # 检查vercel CLI
    code, _, _ = run_cmd(["vercel", "--version"])
    if code != 0:
        code, _, _ = run_cmd(["npm", "install", "-g", "vercel"], timeout=120)
    
    try:
        env = os.environ.copy()
        if token:
            env["VERCEL_TOKEN"] = token
        
        code, out, err = run_cmd(
            ["vercel", "--yes", "--prod", str(DIST_DIR)],
            timeout=180
        )
        
        if code == 0:
            import re
            urls = re.findall(r'https://[^\s]+\.vercel\.app', out + err)
            return urls[0] if urls else None
    except Exception as e:
        log(f"Vercel 部署失败: {e}", "WARN")
    
    return None

def deploy_surge() -> Optional[str]:
    """部署到 Surge.sh"""
    log("尝试部署到 Surge.sh...")
    
    # 检查surge CLI
    code, _, _ = run_cmd(["surge", "--version"])
    if code != 0:
        code, _, _ = run_cmd(["npm", "install", "-g", "surge"], timeout=60)
    
    domain = f"{PROJECT_NAME}.surge.sh"
    
    try:
        # Surge可能需要交互，尝试使用token
        token = os.environ.get("SURGE_TOKEN")
        if token:
            code, out, err = run_cmd(
                ["surge", str(DIST_DIR), domain, "--token", token],
                timeout=60
            )
        else:
            # 尝试匿名部署
            code, out, err = run_cmd(
                ["surge", str(DIST_DIR), domain],
                timeout=60
            )
        
        output = out + err
        if code == 0 or "Success" in output or domain in output:
            return f"https://{domain}"
    except Exception as e:
        log(f"Surge 部署失败: {e}", "WARN")
    
    return None

def deploy_github_pages() -> Optional[str]:
    """部署到 GitHub Pages"""
    log("尝试部署到 GitHub Pages...")
    
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "user/hd-exam-system")
    
    if not token:
        log("未配置 GITHUB_TOKEN", "WARN")
        return None
    
    try:
        # 使用gh-pages分支部署
        branch = "gh-pages"
        repo_url = f"https://x-access-token:{token}@github.com/{repo}.git"
        
        # 创建临时git仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            # 初始化git
            run_cmd(["git", "init"], cwd=tmpdir)
            run_cmd(["git", "config", "user.email", "deploy@bot.com"], cwd=tmpdir)
            run_cmd(["git", "config", "user.name", "Deploy Bot"], cwd=tmpdir)
            
            # 复制文件
            for item in DIST_DIR.iterdir():
                if item.is_file():
                    shutil.copy(item, Path(tmpdir) / item.name)
                else:
                    shutil.copytree(item, Path(tmpdir) / item.name)
            
            # 添加.nojekyll
            with open(Path(tmpdir) / ".nojekyll", "w") as f:
                f.write("")
            
            # 提交并推送
            run_cmd(["git", "add", "."], cwd=tmpdir)
            run_cmd(["git", "commit", "-m", "Deploy"], cwd=tmpdir)
            run_cmd(["git", "branch", "-M", branch], cwd=tmpdir)
            code, out, err = run_cmd(
                ["git", "push", "-f", repo_url, branch],
                cwd=tmpdir, timeout=60
            )
            
            if code == 0:
                return f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}"
    except Exception as e:
        log(f"GitHub Pages 部署失败: {e}", "WARN")
    
    return None

def deploy_netlify() -> Optional[str]:
    """部署到 Netlify"""
    log("尝试部署到 Netlify...")
    
    token = os.environ.get("NETLIFY_TOKEN")
    
    # 检查netlify CLI
    code, _, _ = run_cmd(["netlify", "--version"])
    if code != 0:
        code, _, _ = run_cmd(["npm", "install", "-g", "netlify-cli"], timeout=120)
    
    try:
        if token:
            code, out, err = run_cmd(
                ["netlify", "deploy", "--prod", "--dir", str(DIST_DIR)],
                timeout=120,
                env={**os.environ, "NETLIFY_AUTH_TOKEN": token}
            )
        else:
            code, out, err = run_cmd(
                ["netlify", "deploy", "--prod", "--dir", str(DIST_DIR)],
                timeout=120
            )
        
        output = out + err
        if code == 0 or "Deployed" in output:
            import re
            urls = re.findall(r'https://[^\s]+\.netlify\.app', output)
            return urls[0] if urls else None
    except Exception as e:
        log(f"Netlify 部署失败: {e}", "WARN")
    
    return None

def deploy_static_file_host() -> Optional[str]:
    """使用静态文件托管服务 (0x0.st)"""
    log("尝试使用静态文件托管...")
    
    try:
        # 创建zip包
        zip_path = DIST_DIR.with_suffix('.zip')
        shutil.make_archive(str(DIST_DIR), 'zip', DIST_DIR)
        
        # 使用0x0.st上传
        code, out, err = run_cmd(
            ["curl", "-F", f"file=@{zip_path}", "https://0x0.st"],
            timeout=60
        )
        
        if code == 0 and out.strip():
            return out.strip()
    except Exception as e:
        log(f"文件托管上传失败: {e}", "WARN")
    finally:
        zip_path = DIST_DIR.with_suffix('.zip')
        if zip_path.exists():
            zip_path.unlink()
    
    return None

def generate_instructions():
    """生成手动部署说明"""
    return f"""
{Colors.BOLD}手动部署说明{Colors.RESET}

{Colors.BLUE}1. Cloudflare Pages (推荐){Colors.RESET}
   访问: https://dash.cloudflare.com → Pages → Create project
   上传目录: {DIST_DIR}
   或运行: CLOUDFLARE_API_TOKEN=xxx CLOUDFLARE_ACCOUNT_ID=xxx python scripts/deploy_static.py

{Colors.BLUE}2. GitHub Pages{Colors.RESET}
   创建仓库并上传 {DIST_DIR} 目录
   Settings → Pages → 选择分支
   
{Colors.BLUE}3. Vercel{Colors.RESET}
   访问: https://vercel.com/new
   拖拽上传 {DIST_DIR} 目录

{Colors.BLUE}4. Netlify{Colors.RESET}
   访问: https://app.netlify.com/drop
   拖拽上传 {DIST_DIR} 目录

{Colors.BLUE}5. Surge.sh{Colors.RESET}
   npm install -g surge
   surge {DIST_DIR} hd-exam-system.surge.sh

{Colors.BLUE}部署文件位置{Colors.RESET}
   {DIST_DIR}
   包含: {len(list(DIST_DIR.iterdir()))} 个文件
"""

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  火电机组考核系统 - 自动部署工具")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # 准备文件
    if not prepare_dist():
        return 1
    
    # 尝试各种部署方式
    url = None
    
    deployers = [
        ("Cloudflare Pages", deploy_cloudflare),
        ("Vercel", deploy_vercel),
        ("Netlify", deploy_netlify),
        ("Surge.sh", deploy_surge),
        ("GitHub Pages", deploy_github_pages),
    ]
    
    for name, deploy_func in deployers:
        print()
        url = deploy_func()
        if url:
            break
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    if url:
        print(f"""
{Colors.GREEN}✅ 部署成功!{Colors.RESET}

{Colors.BOLD}🌐 访问地址: {url}{Colors.RESET}

📋 功能说明:
   • 学生考试: 直接访问首页
   • 测试账号: 123456
   • 教师账号: 654321
""")
        
        # 保存部署信息
        deploy_info = {
            "url": url,
            "deploy_time": datetime.now().isoformat(),
            "project": PROJECT_NAME,
            "platform": name
        }
        with open(PROJECT_ROOT / "deploy_info.json", "w", encoding="utf-8") as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        return 0
    else:
        print(generate_instructions())
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n部署已取消")
        sys.exit(1)
