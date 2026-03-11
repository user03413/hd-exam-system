# 部署说明

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.10 |
| pip | 最新版本 |

---

## 快速部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 必需
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="https://integration.coze.cn/api/v3"

# 可选
export COZE_WORKSPACE_PATH="/workspace/projects"
```

### 3. 准备数据文件

将以下文件放到 `assets/` 目录：

```
assets/
├── 火电机组考核学生名单.xlsx
└── 《火电厂热工自动控制技术及应用》_100题.xlsx
```

### 4. 启动服务

```bash
# 默认端口 5000
python src/main.py

# 指定端口
python src/main.py -p 8080
```

### 5. 访问系统

打开浏览器访问：
- 考试入口：`http://localhost:5000/exam/real`

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/
COPY assets/ ./assets/
COPY config/ ./config/

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "src/main.py", "-p", "5000"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t firepower-exam-system .

# 运行容器
docker run -d \
  -p 5000:5000 \
  -e COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key" \
  -e COZE_INTEGRATION_MODEL_BASE_URL="https://integration.coze.cn/api/v3" \
  -v $(pwd)/assets:/app/assets \
  firepower-exam-system
```

---

## Coze 平台部署

### 1. 导入项目

将 `skill.json` 导入到 Coze 平台。

### 2. 配置技能

在技能配置页面添加以下依赖：
- LLM (大语言模型)
- Web Search (联网搜索)
- Document Generation (文档生成)

### 3. 上传数据文件

在项目资源管理器中上传：
- 学生名单 Excel
- 题库 Excel

### 4. 部署上线

点击"部署"按钮，系统会自动分配访问域名。

---

## Trae 平台部署

### 1. 创建项目

在 Trae 控制台创建新项目。

### 2. 上传文件

上传整个项目文件夹，包括：
- `src/` 源代码目录
- `assets/` 数据文件目录
- `config/` 配置目录
- `requirements.txt` 依赖文件

### 3. 配置环境

在环境变量中设置：
```
COZE_WORKLOAD_IDENTITY_API_KEY=your-api-key
COZE_INTEGRATION_MODEL_BASE_URL=https://integration.coze.cn/api/v3
```

### 4. 启动服务

配置启动命令：
```
python src/main.py -p $PORT
```

---

## 生产环境配置

### 环境变量

```bash
# 生产环境配置
COZE_WORKLOAD_IDENTITY_API_KEY=prod-api-key
COZE_INTEGRATION_MODEL_BASE_URL=https://integration.coze.cn/api/v3
COZE_WORKSPACE_PATH=/app
LOG_LEVEL=INFO
```

### 日志配置

日志文件位置：`/app/work/logs/bypass/app.log`

```python
# 日志级别
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 性能调优

```bash
# 使用 gunicorn 运行（推荐生产环境）
gunicorn src.main:app -w 4 -b 0.0.0.0:5000

# 使用 uvicorn 运行
uvicorn src.main:app --host 0.0.0.0 --port 5000 --workers 4
```

---

## 监控和运维

### 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/

# 检查 API 状态
curl -X POST http://localhost:5000/api/exam/verify \
  -H "Content-Type: application/json" \
  -d '{"student_id": "220252216068"}'
```

### 日志查看

```bash
# 查看实时日志
tail -f /app/work/logs/bypass/app.log

# 查看错误日志
grep "ERROR" /app/work/logs/bypass/app.log
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 服务启动失败 | 检查端口是否被占用 |
| 学号验证失败 | 检查学生名单文件路径 |
| 报告导出失败 | 检查 API Key 是否正确 |
| 前沿拓展加载慢 | 检查网络连接 |

---

## 更新维护

### 更新代码

```bash
git pull origin main
pip install -r requirements.txt
# 重启服务
```

### 更新数据文件

直接替换 `assets/` 目录下的 Excel 文件，无需重启服务。

### 备份数据

定期备份以下内容：
- 学生名单 Excel
- 题库 Excel
- 配置文件
