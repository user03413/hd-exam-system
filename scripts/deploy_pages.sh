#!/bin/bash
# 火电机组考核系统 - Cloudflare Pages 部署脚本

set -e

echo "=========================================="
echo "  火电机组考核系统 - Cloudflare Pages 部署"
echo "=========================================="
echo ""

# 检查 wrangler
if ! command -v wrangler &> /dev/null; then
    echo "❌ 错误: 未安装 wrangler"
    echo "请运行: npm install -g wrangler"
    exit 1
fi

# 检查 API Token
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "⚠️  警告: 未设置 CLOUDFLARE_API_TOKEN 环境变量"
    echo ""
    echo "请设置环境变量后重试:"
    echo "  export CLOUDFLARE_API_TOKEN='your_token'"
    echo "  export CLOUDFLARE_ACCOUNT_ID='57d6cde2e053b14fd28bd963ddb0975b'"
    echo ""
    echo "获取 API Token: https://dash.cloudflare.com/profile/api-tokens"
    exit 1
fi

# 设置默认 Account ID
export CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID:-"57d6cde2e053b14fd28bd963ddb0975b"}

# 进入项目目录
cd "$(dirname "$0")/.."
DIST_DIR="dist"

# 检查 dist 目录
if [ ! -d "$DIST_DIR" ]; then
    echo "❌ 错误: dist 目录不存在"
    exit 1
fi

echo "📁 dist 目录内容:"
ls -la "$DIST_DIR/"
echo ""

# 部署到 Cloudflare Pages
echo "🚀 开始部署到 Cloudflare Pages..."
wrangler pages deploy "$DIST_DIR" --project-name=hd-exam-system

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo ""
echo "🔗 访问地址:"
echo "  首页: https://hd-exam-system.pages.dev"
echo "  考试: https://hd-exam-system.pages.dev/exam"
echo "  管理: https://hd-exam-system.pages.dev/teacher"
echo "=========================================="
