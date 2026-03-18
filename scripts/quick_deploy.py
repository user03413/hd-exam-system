#!/usr/bin/env python3
"""
快速部署脚本 - 使用 Tiiny.host 或 Static.app
这些服务不需要认证，可以快速获得永久链接
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"

PROJECT_NAME = "hd-exam-system"

def prepare_dist() -> bool:
    """准备部署目录"""
    print("准备部署文件...")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    
    # 复制离线版HTML
    offline_html = ASSETS_DIR / "火电机组考核系统_离线版.html"
    if not offline_html.exists():
        print(f"错误: 离线版HTML不存在")
        return False
    
    shutil.copy(offline_html, DIST_DIR / "index.html")
    
    # 复制资源文件
    for item in ASSETS_DIR.iterdir():
        if item.is_file():
            shutil.copy(item, DIST_DIR / item.name)
    
    print(f"✓ 部署目录: {len(list(DIST_DIR.iterdir()))} 个文件")
    return True

def deploy_to_tiiny() -> Optional[str]:
    """部署到 tiiny.host"""
    print("正在部署到 tiiny.host...")
    
    try:
        import requests
        import zipfile
        import time
        
        # 创建zip文件
        zip_path = DIST_DIR.with_suffix('.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in DIST_DIR.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(DIST_DIR))
        
        # 上传到tiiny.host
        subdomain = f"{PROJECT_NAME}-{int(time.time())}"
        
        with open(zip_path, 'rb') as f:
            files = {'file': (f'{PROJECT_NAME}.zip', f, 'application/zip')}
            data = {'subdomain': subdomain}
            
            response = requests.post(
                'https://api.tiiny.host/upload',
                files=files,
                data=data,
                timeout=60
            )
        
        zip_path.unlink()
        
        if response.status_code == 200:
            result = response.json()
            return result.get('url') or f"https://{subdomain}.tiiny.site"
            
    except ImportError:
        print("需要安装 requests 库")
    except Exception as e:
        print(f"tiiny.host 部署失败: {e}")
    
    return None

def deploy_to_fleek() -> Optional[str]:
    """部署到 Fleek (IPFS)"""
    print("正在部署到 Fleek (IPFS)...")
    
    try:
        import requests
        
        # 使用IPFS上传
        files = []
        for file in DIST_DIR.rglob('*'):
            if file.is_file():
                rel_path = file.relative_to(DIST_DIR)
                files.append(('file', (str(rel_path), open(file, 'rb'))))
        
        # 上传到IPFS网关
        response = requests.post(
            'https://ipfs.infura.io:5001/api/v0/add',
            files=files,
            timeout=120
        )
        
        if response.status_code == 200:
            # 解析CID
            for line in response.text.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    if 'Hash' in data:
                        return f"https://ipfs.io/ipfs/{data['Hash']}"
                        
    except Exception as e:
        print(f"Fleek/IPFS 部署失败: {e}")
    
    return None

def create_github_pages_workflow() -> str:
    """创建 GitHub Actions 工作流"""
    workflow_dir = PROJECT_ROOT / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_content = """name: Deploy to GitHub Pages

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'dist'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""
    
    workflow_file = workflow_dir / "deploy.yml"
    with open(workflow_file, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    
    return str(workflow_file)

def main():
    """主函数"""
    import time
    
    print("\n" + "=" * 60)
    print("  火电机组考核系统 - 快速部署")
    print("=" * 60 + "\n")
    
    # 准备文件
    if not prepare_dist():
        return 1
    
    # 创建GitHub Actions工作流
    workflow_file = create_github_pages_workflow()
    print(f"✓ 已创建 GitHub Actions 工作流: {workflow_file}")
    
    # 尝试部署
    url = deploy_to_tiiny()
    
    if url:
        print("\n" + "=" * 60)
        print(f"✅ 部署成功!")
        print(f"🌐 永久访问链接: {url}")
        print("=" * 60 + "\n")
        
        deploy_info = {
            "url": url,
            "deploy_time": datetime.now().isoformat(),
            "project": PROJECT_NAME
        }
        with open(PROJECT_ROOT / "deploy_info.json", "w", encoding="utf-8") as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        
        return 0
    
    # 提供手动部署说明
    print("\n" + "=" * 60)
    print("自动部署失败，请使用以下手动部署方式:\n")
    print("方式1: GitHub Pages (推荐)")
    print("  1. 将代码推送到GitHub仓库")
    print("  2. 在仓库设置中启用 GitHub Pages")
    print("  3. 访问 https://<用户名>.github.io/<仓库名>\n")
    print("方式2: Cloudflare Pages")
    print("  1. 访问 https://dash.cloudflare.com")
    print("  2. 进入 Pages → Create project")
    print("  3. 上传 dist 目录\n")
    print("方式3: Vercel")
    print("  1. 访问 https://vercel.com/new")
    print("  2. 拖拽上传 dist 目录\n")
    print("方式4: Netlify Drop")
    print("  1. 访问 https://app.netlify.com/drop")
    print("  2. 拖拽上传 dist 目录\n")
    print(f"部署文件位置: {DIST_DIR}")
    print("=" * 60 + "\n")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
