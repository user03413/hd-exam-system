#!/usr/bin/env python3
"""
Cloudflare Pages 一键部署脚本
自动将火电机组考核系统部署到Cloudflare Pages
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"

PROJECT_NAME = "hd-exam-system"

def log(msg: str, level: str = "INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": "\033[92m", "WARN": "\033[93m", "ERROR": "\033[91m", "RESET": "\033[0m"}
    color = colors.get(level, "")
    reset = colors["RESET"]
    print(f"{color}[{timestamp}] {msg}{reset}")

def run_cmd(cmd: list, cwd: str = None, timeout: int = 120) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or str(PROJECT_ROOT)
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令超时"
    except Exception as e:
        return -1, "", str(e)

def check_node():
    """检查Node.js"""
    code, out, err = run_cmd(["node", "--version"])
    if code == 0:
        log(f"✓ Node.js: {out.strip()}")
        return True
    log("✗ Node.js 未安装，请先安装 Node.js: https://nodejs.org", "ERROR")
    return False

def check_npm():
    """检查npm"""
    code, out, err = run_cmd(["npm", "--version"])
    if code == 0:
        log(f"✓ npm: {out.strip()}")
        return True
    log("✗ npm 未安装", "ERROR")
    return False

def install_wrangler():
    """安装Wrangler"""
    log("正在安装 Wrangler CLI...")
    code, out, err = run_cmd(["npm", "install", "-g", "wrangler"], timeout=180)
    if code == 0:
        log("✓ Wrangler 安装成功")
        return True
    log(f"✗ Wrangler 安装失败: {err}", "ERROR")
    return False

def check_wrangler():
    """检查Wrangler"""
    code, out, err = run_cmd(["wrangler", "--version"])
    if code == 0:
        log(f"✓ Wrangler: {out.strip().split()[0] if out.strip() else 'installed'}")
        return True
    return install_wrangler()

def prepare_dist():
    """准备部署目录"""
    log("准备部署文件...")
    
    # 清理并创建dist目录
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    
    # 1. 复制离线版HTML作为首页
    offline_html = ASSETS_DIR / "火电机组考核系统_离线版.html"
    if not offline_html.exists():
        log(f"✗ 离线版HTML不存在: {offline_html}", "ERROR")
        return False
    
    shutil.copy(offline_html, DIST_DIR / "index.html")
    log(f"✓ index.html (离线考试系统)")
    
    # 2. 复制其他资源文件
    for item in ASSETS_DIR.iterdir():
        if item.is_file() and not item.name.endswith('.html'):
            shutil.copy(item, DIST_DIR / item.name)
            log(f"✓ {item.name}")
    
    # 3. 创建SPA路由配置
    redirects = """# SPA路由支持
/exam /index.html 200
/teacher /index.html 200
/api/* /index.html 200
"""
    with open(DIST_DIR / "_redirects", "w") as f:
        f.write(redirects)
    
    # 4. 创建安全头配置
    headers = """/*
  X-Frame-Options: SAMEORIGIN
  X-Content-Type-Options: nosniff
  Cache-Control: public, max-age=3600
"""
    with open(DIST_DIR / "_headers", "w") as f:
        f.write(headers)
    
    log(f"✓ 部署目录准备完成: {len(list(DIST_DIR.iterdir()))} 个文件")
    return True

def deploy():
    """执行部署"""
    log(f"开始部署到 Cloudflare Pages: {PROJECT_NAME}")
    
    # 使用wrangler部署
    code, out, err = run_cmd(
        ["wrangler", "pages", "deploy", str(DIST_DIR), 
         "--project-name", PROJECT_NAME,
         "--commit-dirty=true"],
        timeout=300
    )
    
    # 解析输出
    output = out + err
    
    if code == 0 or "Success" in output or "Deployed" in output:
        log("✓ 部署成功!")
        
        # 提取URL
        import re
        urls = re.findall(r'https://[^\s,\n]+\.pages\.dev', output)
        if urls:
            return urls[0]
        
        # 构造默认URL
        return f"https://{PROJECT_NAME}.pages.dev"
    
    # 检查是否需要登录
    if "login" in output.lower() or "auth" in output.lower():
        log("需要登录 Cloudflare，正在启动交互式登录...", "WARN")
        log("请在弹出的浏览器中完成登录，然后重新运行此脚本")
        
        # 尝试交互式部署
        try:
            subprocess.run(
                ["wrangler", "pages", "deploy", str(DIST_DIR), 
                 "--project-name", PROJECT_NAME],
                cwd=str(PROJECT_ROOT)
            )
        except KeyboardInterrupt:
            pass
        return None
    
    log(f"✗ 部署失败: {err or output}", "ERROR")
    return None

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  火电机组考核系统 - Cloudflare Pages 部署工具")
    print("=" * 60 + "\n")
    
    # 1. 检查环境
    log("检查部署环境...")
    if not check_node() or not check_npm():
        return 1
    if not check_wrangler():
        return 1
    print()
    
    # 2. 准备文件
    if not prepare_dist():
        return 1
    print()
    
    # 3. 部署
    url = deploy()
    
    print("\n" + "=" * 60)
    if url:
        log("🎉 部署成功!", "INFO")
        print(f"""
  ✅ 火电机组考核系统已部署
  
  📍 永久访问地址: {url}
  
  📋 功能说明:
     • 学生考试: 直接访问首页
     • 测试账号: 123456
     • 教师账号: 654321
  
  💡 提示:
     • Cloudflare Pages 自动提供 HTTPS
     • 每次部署会更新内容
     • 可在 Cloudflare Dashboard 管理项目
""")
        # 保存部署信息
        deploy_info = {
            "url": url,
            "deploy_time": datetime.now().isoformat(),
            "project": PROJECT_NAME
        }
        with open(PROJECT_ROOT / "deploy_info.json", "w", encoding="utf-8") as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        print("=" * 60 + "\n")
        return 0
    else:
        log("❌ 部署失败", "ERROR")
        print("""
  请尝试以下步骤:
  1. 运行 'wrangler login' 登录 Cloudflare
  2. 重新运行此脚本
  
  或手动部署:
  1. 访问 https://dash.cloudflare.com
  2. 进入 Pages > Create a project
  3. 上传 dist 目录中的文件
""")
        print("=" * 60 + "\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n部署已取消")
        sys.exit(1)
