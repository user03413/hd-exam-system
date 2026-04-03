#!/usr/bin/env python3
"""
将火电机组考核系统部署到对象存储
生成永久访问链接
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"

PROJECT_NAME = "hd-exam-system"

def log(msg: str, level: str = "INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": "\033[92m", "WARN": "\033[93m", "ERROR": "\033[91m"}
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{timestamp}] {msg}{reset}")

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
    
    log(f"✓ 部署目录: {len(list(DIST_DIR.iterdir()))} 个文件")
    return True

def deploy_to_storage() -> Optional[str]:
    """部署到对象存储"""
    log("正在部署到对象存储...")
    
    try:
        from coze_coding_dev_sdk.s3 import S3SyncStorage
        
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key="",
            secret_key="",
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )
        
        uploaded_files = []
        base_prefix = f"exam-system/{int(datetime.now().timestamp())}"
        
        # 上传所有文件
        for file_path in DIST_DIR.iterdir():
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # 清理文件名（移除中文和特殊字符）
                safe_name = file_path.name
                # 替换中文字符
                import re
                safe_name = re.sub(r'[^\x00-\x7F]', '_', safe_name)
                safe_name = re.sub(r'[?#&%{}^[\]`\\<>\~|"\'+=:;]', '_', safe_name)
                safe_name = safe_name.replace(' ', '_')
                
                # 确定content-type
                content_type = "application/octet-stream"
                if file_path.suffix == '.html':
                    content_type = "text/html"
                elif file_path.suffix == '.css':
                    content_type = "text/css"
                elif file_path.suffix == '.js':
                    content_type = "application/javascript"
                elif file_path.suffix in ['.png', '.jpg', '.jpeg', '.gif']:
                    content_type = f"image/{file_path.suffix[1:]}"
                elif file_path.suffix == '.xlsx':
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                
                key = storage.upload_file(
                    file_content=content,
                    file_name=f"{base_prefix}/{safe_name}",
                    content_type=content_type,
                )
                
                uploaded_files.append((safe_name, key))
                log(f"✓ 上传: {safe_name}")
        
        # 生成主页URL（设置较长的有效期）
        index_key = None
        for name, key in uploaded_files:
            if name == 'index.html' or name.startswith('index'):
                index_key = key
                break
        
        if index_key:
            # 生成30天有效的URL
            url = storage.generate_presigned_url(
                key=index_key,
                expire_time=2592000  # 30天
            )
            return url
        
    except ImportError as e:
        log(f"缺少依赖: {e}", "ERROR")
        log("请安装: pip install coze-coding-dev-sdk", "WARN")
    except Exception as e:
        log(f"上传失败: {e}", "ERROR")
    
    return None

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  火电机组考核系统 - 部署到对象存储")
    print("=" * 60 + "\n")
    
    # 准备文件
    if not prepare_dist():
        return 1
    
    # 部署
    url = deploy_to_storage()
    
    print("\n" + "=" * 60)
    
    if url:
        print(f"""
✅ 部署成功!

🌐 访问链接: {url}
   (链接有效期30天)

📋 功能说明:
   • 学生考试: 直接访问链接
   • 测试账号: 123456
   • 教师账号: 654321

💡 提示:
   • 此链接可直接用于考试
   • 如需永久链接，请使用Cloudflare Pages
""")
        
        # 保存部署信息
        deploy_info = {
            "url": url,
            "deploy_time": datetime.now().isoformat(),
            "project": PROJECT_NAME,
            "type": "object_storage"
        }
        with open(PROJECT_ROOT / "deploy_info.json", "w", encoding="utf-8") as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        
        print("=" * 60 + "\n")
        return 0
    else:
        print("""
❌ 部署失败

请确保:
1. 已设置环境变量 COZE_BUCKET_ENDPOINT_URL
2. 已设置环境变量 COZE_BUCKET_NAME
3. 网络连接正常

或使用手动部署:
1. 访问 https://dash.cloudflare.com
2. 进入 Pages → Create project
3. 上传 dist 目录
""")
        print("=" * 60 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
