#!/usr/bin/env python3
"""
Cloudflare Pages 自动部署脚本
将火电机组考核系统部署到Cloudflare Pages，返回永久网页链接
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"

def log(msg: str, level: str = "INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def check_dependencies():
    """检查依赖"""
    log("检查部署依赖...")
    
    # 检查Node.js和npm
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        log(f"Node.js 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        log("Node.js 未安装，尝试安装...", "WARN")
        return False
    
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        log(f"npm 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        log("npm 未安装", "ERROR")
        return False
    
    return True

def install_wrangler():
    """安装Wrangler CLI"""
    log("安装 Wrangler CLI...")
    try:
        result = subprocess.run(
            ["npm", "install", "-g", "wrangler"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            log("Wrangler 安装成功")
            return True
        else:
            log(f"Wrangler 安装失败: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"安装异常: {e}", "ERROR")
        return False

def prepare_dist():
    """准备部署文件"""
    log("准备部署文件...")
    
    # 创建dist目录
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    
    # 复制离线版HTML
    offline_html = ASSETS_DIR / "火电机组考核系统_离线版.html"
    if offline_html.exists():
        shutil.copy(offline_html, DIST_DIR / "index.html")
        log(f"复制离线版HTML: {offline_html.name} -> index.html")
    else:
        log(f"离线版HTML不存在: {offline_html}", "ERROR")
        return False
    
    # 复制assets目录中的其他资源
    for item in ASSETS_DIR.iterdir():
        if item.is_file() and not item.name.endswith('.html'):
            shutil.copy(item, DIST_DIR / item.name)
            log(f"复制资源文件: {item.name}")
    
    # 创建_redirects文件（处理路由）
    redirects_content = """# Cloudflare Pages 重定向规则
/exam /index.html 200
/teacher /index.html 200
/* /index.html 404
"""
    with open(DIST_DIR / "_redirects", "w", encoding="utf-8") as f:
        f.write(redirects_content)
    
    # 创建_headers文件（安全头）
    headers_content = """/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
"""
    with open(DIST_DIR / "_headers", "w", encoding="utf-8") as f:
        f.write(headers_content)
    
    log(f"部署文件准备完成: {DIST_DIR}")
    return True

def create_wrangler_config():
    """创建wrangler配置"""
    log("创建Wrangler配置...")
    
    wrangler_toml = PROJECT_ROOT / "wrangler.toml"
    config_content = """# Cloudflare Pages 配置
name = "hd-exam-system"
compatibility_date = "2024-01-01"

[site]
bucket = "./dist"

[build]
command = "echo 'Static site, no build needed'"
"""
    with open(wrangler_toml, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    log(f"Wrangler配置已创建: {wrangler_toml}")
    return True

def deploy_with_api():
    """使用Cloudflare API部署（不需要安装wrangler）"""
    log("使用Cloudflare API部署...")
    
    # 检查环境变量
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    
    if not api_token or not account_id:
        log("未找到Cloudflare API配置，尝试使用Wrangler...", "WARN")
        return None
    
    try:
        import requests
        
        # 创建Pages项目
        project_name = "hd-exam-system"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # 检查项目是否存在
        check_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}"
        resp = requests.get(check_url, headers=headers)
        
        if resp.status_code != 200:
            # 创建项目
            create_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
            create_data = {
                "name": project_name,
                "production_branch": "main"
            }
            resp = requests.post(create_url, headers=headers, json=create_data)
            if resp.status_code not in [200, 201]:
                log(f"创建项目失败: {resp.text}", "ERROR")
                return None
        
        # 上传文件
        upload_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/deployments"
        
        # 准备文件列表
        files = []
        for file_path in DIST_DIR.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(DIST_DIR)
                files.append(("file", (str(rel_path), open(file_path, "rb"), "application/octet-stream")))
        
        # 上传部署
        headers_multipart = {
            "Authorization": f"Bearer {api_token}"
        }
        resp = requests.post(upload_url, headers=headers_multipart, files=files)
        
        if resp.status_code in [200, 201]:
            result = resp.json()
            if result.get("success"):
                deployment = result.get("result", {})
                url = deployment.get("url") or f"https://{project_name}.pages.dev"
                return url
        
        log(f"部署失败: {resp.text}", "ERROR")
        return None
        
    except ImportError:
        log("requests模块未安装，尝试安装...", "WARN")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
        return deploy_with_api()
    except Exception as e:
        log(f"API部署异常: {e}", "ERROR")
        return None

def deploy_with_wrangler():
    """使用Wrangler CLI部署"""
    log("使用Wrangler CLI部署...")
    
    # 检查wrangler是否安装
    try:
        result = subprocess.run(
            ["wrangler", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            if not install_wrangler():
                return None
    except FileNotFoundError:
        if not install_wrangler():
            return None
    
    # 执行部署
    try:
        log("开始部署到Cloudflare Pages...")
        result = subprocess.run(
            ["wrangler", "pages", "deploy", str(DIST_DIR), "--project-name=hd-exam-system"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode == 0:
            log("部署成功！")
            # 解析输出获取URL
            output = result.stdout + result.stderr
            # 查找部署URL
            import re
            url_pattern = r'https://[a-zA-Z0-9-]+\.pages\.dev'
            urls = re.findall(url_pattern, output)
            if urls:
                return urls[0]
            
            # 默认URL
            return "https://hd-exam-system.pages.dev"
        else:
            log(f"部署失败: {result.stderr}", "ERROR")
            log(f"标准输出: {result.stdout}", "DEBUG")
            return None
            
    except subprocess.TimeoutExpired:
        log("部署超时", "ERROR")
        return None
    except Exception as e:
        log(f"部署异常: {e}", "ERROR")
        return None

def deploy_to_cloudflare():
    """主部署函数"""
    log("=" * 60)
    log("Cloudflare Pages 自动部署脚本")
    log("=" * 60)
    
    # 1. 检查依赖
    if not check_dependencies():
        log("依赖检查失败，尝试使用API方式...", "WARN")
    
    # 2. 准备部署文件
    if not prepare_dist():
        log("部署文件准备失败", "ERROR")
        return None
    
    # 3. 创建配置
    create_wrangler_config()
    
    # 4. 尝试API部署
    url = deploy_with_api()
    
    # 5. 如果API失败，尝试Wrangler
    if not url:
        url = deploy_with_wrangler()
    
    if url:
        log("=" * 60)
        log(f"🎉 部署成功！")
        log(f"📍 永久访问链接: {url}")
        log("=" * 60)
        
        # 保存部署信息
        deploy_info = {
            "url": url,
            "deploy_time": datetime.now().isoformat(),
            "project_name": "hd-exam-system"
        }
        with open(PROJECT_ROOT / "deploy_info.json", "w", encoding="utf-8") as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        
        return url
    else:
        log("部署失败，请检查配置和网络", "ERROR")
        return None

def main():
    """主入口"""
    url = deploy_to_cloudflare()
    
    if url:
        print(f"\n{'='*60}")
        print(f"✅ 部署成功！")
        print(f"🌐 访问地址: {url}")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"\n{'='*60}")
        print(f"❌ 部署失败")
        print(f"请确保:")
        print(f"1. 已设置 CLOUDFLARE_API_TOKEN 环境变量")
        print(f"2. 已设置 CLOUDFLARE_ACCOUNT_ID 环境变量")
        print(f"3. 或已安装 Node.js 和 Wrangler CLI")
        print(f"{'='*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
