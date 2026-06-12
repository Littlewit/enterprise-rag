# 企业级知识库问答系统

基于 LangChain + Chroma + LangGraph 构建的多租户 RAG（检索增强生成）知识库问答平台，支持多部门文档隔离上传、流式对话和向量持久化存储。

## 📋 目录

- [技术架构](#技术架构)
- [核心功能](#核心功能)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [API 接口规范](#api-接口规范)
- [部署方案](#部署方案)
- [📘 详细操作指南 (DEPLOY.md)](./DEPLOY.md) — GitHub 提交流程 + Docker 部署至阿里云 ECS 完整步骤
- [常见问题](#常见问题)

---

## 技术架构

```
┌─────────────────────┐     ┌──────────────────────────────┐
│   Frontend (HTML)   │────▶│  FastAPI (backend/app.py)    │
│  Glassmorphism UI   │     │  /upload  /chat/stream       │
└─────────────────────┘     └───────────┬──────────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                       ▼
    ┌───────────────────┐   ┌───────────────────┐   ┌──────────────────────┐
    │   RAGPipeline     │   │    RAGGraph       │   │      models.py       │
    │  Chroma 多租户     │   │  LangGraph 工作流  │   │   LLM + Embedding    │
    └────────┬──────────┘   └───────────────────┘   └──────────────────────┘
             │
    ┌────────▼──────────────────────────────────┐
    │         Chroma PersistentClient            │
    │  dept_hr / dept_tech / dept_finance ...   │
    │          (SQLite 持久化)                    │
    └───────────────────────────────────────────┘
```

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| LLM | 阿里千问 `qwen3.6-flash` | 通过 DashScope API 调用 |
| Embedding | `BAAI/bge-small-zh-v1.5` | 中文嵌入模型，本地 CPU 推理 |
| 向量库 | Chroma (PersistentClient) | SQLite 持久化，多 Collection 隔离 |
| 工作流 | LangGraph | 检索→生成 两阶段状态图 |
| Web 框架 | FastAPI + SSE | 流式输出 via `text/event-stream` |
| 前端 | 原生 HTML/CSS/JS | Glassmorphism 风格，EventSource SSE 流式渲染 |

---

## 核心功能

### 1. 多租户文档隔离
- 每个部门独立 Chroma Collection，命名规则 `dept_{department}`
- 上传文档时按部门写入对应 Collection，检索时严格隔离
- 支持 `.txt` `.md` `.pdf` `.docx` `.csv` 五种文档格式

### 2. 流式 AI 问答
- 基于检索到的知识库上下文，由千问 LLM 生成回答
- SSE (Server-Sent Events) 流式输出，前端逐字渲染
- 最多检索 3 条相关文本块作为生成上下文

### 3. 文档智能处理
- 自动分块：500 字符/块，50 字符重叠
- 按中文标点 + 换行符智能切割
- 向量化后持久化到 Chroma，重启不丢失

### 4. 异步并发
- `asyncio.to_thread` 包裹文档处理，不阻塞事件循环
- 不同部门文档可并发上传

---

## 环境要求

| 依赖 | 版本 | 备注 |
|------|------|------|
| Python | ≥ 3.13 | 推荐使用 [uv](https://docs.astral.sh/uv/) 管理 |
| uv | 最新版 | Python 包管理器 |

### 模型下载

首次运行会自动从 ModelScope 下载 Embedding 模型（约 100MB），请确保网络畅通。

### API Key

需要阿里云 DashScope API Key，[免费申请](https://dashscope.console.aliyun.com/apiKey)。

---

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd enterprise-rag

# 或从零初始化并推送（Windows 用户）
# powershell -ExecutionPolicy Bypass -File scripts/github_push.ps1

# 或从零初始化并推送（Linux/Mac 用户）
# bash scripts/github_push.sh
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

> `.env` 文件内容：
> ```
> DASHSCOPE_API_KEY=sk-your-api-key-here
> ```

### 4. 启动服务

```bash
uv run uvicorn backend.app:app --host 0.0.0.0 --port 7860 --reload
```

### 5. 打开前端

浏览器访问 `http://localhost:7860`，输入部门名称后即可开始使用。

---

## 项目结构

```
enterprise-rag/
├── backend/                    # 后端核心模块
│   ├── __init__.py
│   ├── app.py                  # FastAPI 接口层（路由、校验、SSE）
│   ├── config.py               # 全局配置常量
│   ├── models.py               # LLM + Embedding 模型惰性单例
│   ├── rag_pipeline.py         # 文档加载、分块、向量化、多租户检索
│   ├── graph_workflow.py       # LangGraph 检索→生成工作流
│   └── static/
│       └── index.html          # 前端聊天界面
├── data/                       # 运行时数据
│   └── chroma/                 # Chroma 向量库持久化目录（自动创建）
├── models/                     # 本地模型文件（自动下载）
│   └── bge-small-zh/           # BGE 嵌入模型
├── pyproject.toml              # 项目元信息与依赖声明
├── uv.lock                     # 依赖锁定文件
├── .gitignore
├── .env.example                # 环境变量模板
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # 容器编排
├── scripts/                    # 辅助脚本
│   ├── github_push.sh          # Linux/Mac GitHub 推送脚本
│   └── github_push.ps1         # Windows GitHub 推送脚本
└── README.md
```

---

## 配置说明

所有可调参数集中在 `backend/config.py`，支持通过 `.env` 覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_MODEL_NAME` | `qwen3.6-flash` | 阿里千问模型 |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API 端点 |
| `DASHSCOPE_API_KEY` | 从 `.env` 读取 | API 密钥（必填） |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-small-zh-v1.5` | 嵌入模型 |
| `EMBEDDING_DEVICE` | `cpu` | 推理设备（cpu / cuda） |
| `CHUNK_SIZE` | `500` | 文本块大小（字符） |
| `CHUNK_OVERLAP` | `50` | 文本块重叠量 |
| `RETRIEVER_TOP_K` | `3` | 检索返回数量 |
| `CHROMA_PERSIST_DIR` | `data/chroma` | 向量库存储路径 |
| `MAX_UPLOAD_SIZE_BYTES` | `50MB` | 上传文件大小上限 |
| `ALLOWED_UPLOAD_EXTENSIONS` | `.txt .pdf .docx .md .csv` | 允许的文件类型 |

---

## API 接口规范

### 基础信息

- **Base URL**: `http://localhost:7860`
- **Content-Type**: `application/json`（上传使用 `multipart/form-data`）

---

### `GET /` — 前端聊天界面

返回 Glassmorphism 风格的单页聊天应用。

---

### `POST /upload` — 上传文档

将文档解析并存入指定部门的知识库。

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `department` | Query | string | ✅ | 部门名称（1-32 字符，中英文/数字/下划线） |
| `file` | Body (form) | file | ✅ | 上传文件（≤ 50MB，支持 .txt .pdf .docx .md .csv） |

**响应示例**：

```json
// 200 OK
{
  "message": "产品手册.pdf 已存入部门 [技术部] 知识库"
}

// 400 Bad Request
{
  "detail": "不支持的文件类型: .xlsx，允许的类型: .csv, .docx, .md, .pdf, .txt"
}

// 500 Internal Server Error
{
  "detail": "文档处理失败: 文档内容为空"
}
```

**cURL 示例**：

```bash
curl -X POST "http://localhost:7860/upload?department=技术部" \
  -F "file=@产品手册.pdf"
```

---

### `GET /chat/stream` — 流式问答

基于部门知识库进行流式 AI 问答（SSE 协议）。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 问题内容（1-2000 字符） |
| `department` | string | ✅ | 部门名称 |

**响应格式**：`text/event-stream`（SSE）

```
data: 根据知识库显示，
data: 产品A的主要功能包括...
data: [DONE]
```

**SSE 事件说明**：

| 事件数据 | 含义 |
|----------|------|
| `data: <文本片段>` | LLM 流式输出的文本块 |
| `data: [DONE]` | 流式输出完成 |
| `data: [ERROR] <错误信息>` | 处理异常（部门知识库为空、LLM 调用失败等） |

**前端示例**：

```javascript
const params = new URLSearchParams({ query: "产品功能", department: "技术部" });
const es = new EventSource(`/chat/stream?${params}`);

es.onmessage = (event) => {
  if (event.data === "[DONE]") {
    es.close();
  } else if (event.data.startsWith("[ERROR]")) {
    console.error(event.data);
    es.close();
  } else {
    // 逐字渲染
    renderChunk(event.data);
  }
};
```

**cURL 示例**：

```bash
curl -N "http://localhost:7860/chat/stream?query=产品有哪些功能&department=技术部"
```

---

### 状态码汇总

| 状态码 | 场景 |
|--------|------|
| 200 | 请求成功 |
| 400 | 参数校验失败（部门名不合法、文件类型不支持、查询过短/过长） |
| 500 | 服务端异常（模型加载失败、文档处理错误、知识库为空） |

---

## 部署方案

### 方式一：Docker 部署（推荐）

#### 1. 构建与启动

```bash
# 构建镜像
docker build -t enterprise-rag:latest .

# 启动服务
docker compose up -d
```

#### 2. 服务管理

```bash
docker compose logs -f          # 查看日志
docker compose restart          # 重启
docker compose down             # 停止并移除容器
```

#### 3. 数据持久化

Docker Compose 将 `data/` 和 `models/` 目录挂载到宿主机，容器重启后向量数据和模型文件不会丢失。

---

### 方式二：原生部署（阿里云 ECS）

以下步骤以 **Alibaba Cloud Linux 3 / CentOS 7+** 为例：

#### 1. 安装 Python 3.13

```bash
# 安装依赖
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel

# 下载编译 Python 3.13
cd /tmp
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar xzf Python-3.13.0.tgz
cd Python-3.13.0
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

# 验证
python3.13 --version
```

#### 2. 安装 uv 包管理器

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### 3. 克隆项目并安装依赖

```bash
git clone <your-repo-url> /opt/enterprise-rag
cd /opt/enterprise-rag

# 配置环境变量
cp .env.example .env
vim .env  # 填入 DASHSCOPE_API_KEY

# 安装依赖
uv sync
```

#### 4. 配置 Systemd 服务

```bash
sudo vim /etc/systemd/system/enterprise-rag.service
```

```ini
[Unit]
Description=Enterprise RAG Service
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/opt/enterprise-rag
EnvironmentFile=/opt/enterprise-rag/.env
ExecStart=/root/.local/bin/uv run uvicorn backend.app:app --host 0.0.0.0 --port 7860
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable enterprise-rag
sudo systemctl start enterprise-rag

# 检查状态
sudo systemctl status enterprise-rag
```

#### 5. Nginx 反向代理（可选，建议配置）

```bash
sudo yum install -y nginx
sudo vim /etc/nginx/conf.d/enterprise-rag.conf
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # SSE 需要关闭缓冲
    location /chat/stream {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;           # SSE 关键配置
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 6. 防火墙配置

```bash
# 阿里云安全组放行 80 端口
# 本地防火墙（如启用）
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --reload
```

---

### 方式三：Docker 部署到阿里云 ECS

1. 在 ECS 上安装 Docker：
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. 上传项目文件到 ECS，执行：
```bash
docker compose up -d
```

3. 验证：
```bash
curl http://localhost:7860/chat/stream?query=你好&department=测试部
```

---

## 常见问题

**Q: 首次启动时 Embedding 模型下载很慢？**
A: 模型从 ModelScope（魔搭社区）下载，国内网络通常较快。如需代理，设置 `MODELSCOPE_CACHE` 环境变量指定缓存路径。

**Q: 如何切换 LLM？**
A: 修改 `backend/config.py` 中的 `LLM_MODEL_NAME` 和 `LLM_BASE_URL`，或通过 `.env` 覆盖。兼容 OpenAI 接口的任何模型都可直接替换。

**Q: 部门名可以使用中文吗？**
A: 可以。系统自动将中文部门名哈希为合法的 Chroma Collection 名（SHA256 前 12 位），数据不受影响。

**Q: 向量数据存储在哪里？**
A: `data/chroma/` 目录下的 SQLite 数据库。备份此目录即可备份所有知识库数据。

**Q: GPU 支持吗？**
A: 将 `EMBEDDING_DEVICE` 改为 `cuda` 即可启用 GPU 加速（需安装 CUDA 版 PyTorch）。

**Q: 支持哪些文档格式？**
A: `.txt` `.md` `.pdf` `.docx` `.csv` 五种。如需扩展，编辑 `ALLOWED_UPLOAD_EXTENSIONS` 和 `rag_pipeline.py` 中的 `_get_loader()` 方法。
