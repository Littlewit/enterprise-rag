# 项目操作指南

本文档提供 enterprise-rag 项目从代码提交到 Docker 部署的完整操作流程。

---

## 目录

- [第一部分：代码提交至 GitHub](#第一部分代码提交至-github)
  - [1.1 Git 初始化与首次提交](#11-git-初始化与首次提交)
  - [1.2 关联远程仓库并推送](#12-关联远程仓库并推送)
  - [1.3 分支管理](#13-分支管理)
  - [1.4 日常提交流程](#14-日常提交流程)
  - [1.5 提交信息规范](#15-提交信息规范)
- [第二部分：Docker 部署至阿里云 ECS](#第二部分docker-部署至阿里云-ecs)
  - [2.1 本地环境准备](#21-本地环境准备)
  - [2.2 本地镜像构建与测试](#22-本地镜像构建与测试)
  - [2.3 推送镜像至阿里云容器镜像服务](#23-推送镜像至阿里云容器镜像服务)
  - [2.4 ECS 服务器环境配置](#24-ecs-服务器环境配置)
  - [2.5 服务器拉取镜像并运行](#25-服务器拉取镜像并运行)
  - [2.6 配置 Nginx 反向代理与域名](#26-配置-nginx-反向代理与域名)
  - [2.7 验证与运维](#27-验证与运维)
- [附录](#附录)

---

## 第一部分：代码提交至 GitHub

### 1.1 Git 初始化与首次提交

**前置条件**：已在 [GitHub](https://github.com) 创建一个**空仓库**（不要勾选 README、.gitignore、LICENSE）。

```bash
# 进入项目根目录
cd enterprise-rag

# 初始化 Git 仓库
git init

# 切换到主分支（GitHub 新仓库默认使用 main）
git checkout -b main
```

> **注意**：本文档统一使用 `main` 作为主分支名。如果你的 GitHub 默认分支为 `master`，将下文所有 `main` 替换为 `master`。

```bash
# 查看当前文件状态
git status

# 添加所有文件到暂存区
git add .

# 再次查看状态，确认纳入版本管理的文件
git status
```

> `.gitignore` 已配置忽略 `.env`、`data/`、`models/`、`__pycache__/` 等文件，这些不会被提交。

```bash
# 创建初始提交
git commit -m "chore: init enterprise-rag project

- 基于 FastAPI + LangChain + Chroma 的多租户 RAG 知识库问答系统
- 支持多部门文档隔离上传与流式 AI 问答
- Docker 容器化部署支持"
```

---

### 1.2 关联远程仓库并推送

```bash
# 添加远程仓库（将 <your-repo-url> 替换为你的仓库地址）
git remote add origin <your-repo-url>

# 示例：
# git remote add origin https://github.com/username/enterprise-rag.git

# 查看远程仓库配置
git remote -v
```

> 如果使用 SSH 方式：
> ```bash
> git remote add origin git@github.com:username/enterprise-rag.git
> ```

```bash
# 推送代码到远程仓库
git push -u origin main

# -u 参数将本地 main 分支与远程 origin/main 建立追踪关系
# 后续只需 git push 即可
```

**验证**：打开 GitHub 仓库页面，确认代码已成功推送。

---

### 1.3 分支管理

```bash
# 查看所有分支
git branch -a

# 创建功能分支
git checkout -b feature/multi-upload

# 在功能分支上开发...
git add .
git commit -m "feat: 支持批量文档上传"

# 推送功能分支到远程
git push -u origin feature/multi-upload

# 切回主分支
git checkout main

# 合并功能分支（通常在 GitHub 上通过 Pull Request 完成）
git merge feature/multi-upload

# 删除本地功能分支
git branch -d feature/multi-upload

# 删除远程功能分支
git push origin --delete feature/multi-upload
```

**推荐分支策略**：

| 分支 | 用途 |
|------|------|
| `main` | 生产就绪代码 |
| `develop` | 开发集成分支 |
| `feature/*` | 新功能开发 |
| `fix/*` | Bug 修复 |
| `release/*` | 发布准备 |

---

### 1.4 日常提交流程

```bash
# 1. 拉取最新代码
git pull

# 2. 查看修改
git status
git diff

# 3. 添加修改并提交
git add .
git commit -m "feat: 增加文档类型支持"

# 4. 推送到远程
git push
```

---

### 1.5 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 增加 Excel 文件解析` |
| `fix` | Bug 修复 | `fix: 修复流式输出截断问题` |
| `docs` | 文档更新 | `docs: 完善 API 接口文档` |
| `refactor` | 代码重构 | `refactor: 抽取文档加载器工厂` |
| `perf` | 性能优化 | `perf: 优化向量检索延迟` |
| `test` | 测试相关 | `test: 增加多租户隔离测试` |
| `chore` | 构建/工具变更 | `chore: 升级 chromadb 到 0.6.0` |

---

## 第二部分：Docker 部署至阿里云 ECS

### 2.1 本地环境准备

**本地开发机要求**：

- Docker ≥ 20.10
- Docker Compose ≥ 2.0
- 已配置阿里云容器镜像服务访问凭证

```bash
# 确认 Docker 版本
docker --version
docker compose version
```

---

### 2.2 本地镜像构建与测试

#### 2.2.1 配置环境变量

```bash
# 确保 .env 文件存在（从模板创建）
cp .env.example .env

# 编辑 .env，填入你的 DashScope API Key
# DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

> ⚠️ `.env` 已在 `.gitignore` 中，不会被提交到 Git 仓库。

#### 2.2.2 构建镜像

```bash
# 在项目根目录下构建
cd enterprise-rag

# 构建镜像（首次构建约 3-5 分钟）
docker build -t enterprise-rag:latest .
```

构建过程说明：
1. **builder 阶段**：基于 `python:3.13-slim`，使用 `uv` 安装依赖
2. **runtime 阶段**：复制虚拟环境 + 应用代码，非 root 用户运行

#### 2.2.3 本地运行验证

```bash
# 方式一：docker compose（推荐）
docker compose up -d

# 方式二：docker run
docker run -d \
  --name enterprise-rag \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  enterprise-rag:latest
```

```bash
# 查看日志
docker logs -f enterprise-rag

# 验证服务
curl http://localhost:8000/
# 应返回 HTML 页面

# 测试 API
curl http://localhost:8000/chat/stream?query=你好&department=测试部
```

```bash
# 停止并清理本地测试容器
docker compose down
# 或
docker stop enterprise-rag && docker rm enterprise-rag
```

---

### 2.3 推送镜像至阿里云容器镜像服务

#### 2.3.1 创建镜像仓库

1. 登录 [阿里云容器镜像服务控制台](https://cr.console.aliyun.com/)
2. 创建**命名空间**（如 `enterprise`）
3. 创建**镜像仓库**（如 `enterprise-rag`），选择"本地仓库"

#### 2.3.2 登录并推送

```bash
# 登录阿里云容器镜像服务
# 地域示例：杭州（cn-hangzhou）、上海（cn-shanghai）、北京（cn-beijing）
docker login --username=<你的阿里云账号> registry.cn-hangzhou.aliyuncs.com

# 给本地镜像打标签
docker tag enterprise-rag:latest \
  registry.cn-hangzhou.aliyuncs.com/<命名空间>/enterprise-rag:latest

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/<命名空间>/enterprise-rag:latest
```

> 示例（假设命名空间为 `enterprise`，地域为杭州）：
> ```bash
> docker tag enterprise-rag:latest registry.cn-hangzhou.aliyuncs.com/enterprise/enterprise-rag:latest
> docker push registry.cn-hangzhou.aliyuncs.com/enterprise/enterprise-rag:latest
> ```

---

### 2.4 ECS 服务器环境配置

**服务器配置建议**：

| 配置项 | 最低要求 | 推荐配置 |
|--------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 系统盘 | 40 GB | 80 GB |
| 操作系统 | Ubuntu 22.04 64 位 | Ubuntu 22.04 64 位 |
| 带宽 | 1 Mbps | 5 Mbps |

> 嵌入模型和 LLM 推理均为 API 调用，对服务器 GPU 无要求，CPU 即可运行。

#### 2.4.1 连接到 ECS 服务器

```bash
# SSH 连接（替换为你的服务器公网 IP）
ssh root@<your-server-ip>

# 如果使用密钥文件
ssh -i ~/.ssh/your-key.pem root@<your-server-ip>
```

#### 2.4.2 安装 Docker

```bash
# 1. 更新软件包索引
sudo apt update

# 2. 安装必要依赖
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. 添加 Docker 软件源
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 启动 Docker 并设置开机自启
sudo systemctl enable docker
sudo systemctl start docker

# 7. 验证安装
sudo docker --version
sudo docker compose version
```

#### 2.4.3 配置非 root 用户使用 Docker（可选）

```bash
# 创建应用用户
sudo useradd -m -s /bin/bash app

# 将用户加入 docker 组
sudo usermod -aG docker app

# 使权限生效（重新登录或执行）
newgrp docker

# 验证
docker ps
```

#### 2.4.4 配置安全组

在阿里云 ECS 控制台 → 安全组 → 入方向规则中添加：

| 端口 | 协议 | 授权对象 | 说明 |
|------|------|---------|------|
| 22 | TCP | 你的 IP/0.0.0.0/0 | SSH 远程连接 |
| 80 | TCP | 0.0.0.0/0 | HTTP（Nginx） |
| 443 | TCP | 0.0.0.0/0 | HTTPS（可选） |

> ⚠️ 8000 端口建议仅对 127.0.0.1 开放（通过 Nginx 反代），或仅限白名单 IP 访问。

#### 2.4.5 服务器防火墙配置（Ubuntu UFW）

```bash
# 如果启用了 UFW 防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 查看状态
sudo ufw status
```

---

### 2.5 服务器拉取镜像并运行

#### 2.5.1 登录阿里云镜像仓库

```bash
# SSH 到服务器后
docker login --username=<你的阿里云账号> registry.cn-hangzhou.aliyuncs.com
```

#### 2.5.2 创建项目目录结构

```bash
# 创建应用目录
sudo mkdir -p /opt/enterprise-rag/{data,models}

# 设置权限
sudo chown -R app:app /opt/enterprise-rag

# 切换到应用用户
sudo su - app
cd /opt/enterprise-rag
```

#### 2.5.3 创建环境变量文件

```bash
# 创建 .env 文件
cat > .env << 'EOF'
DASHSCOPE_API_KEY=sk-your-api-key-here
EOF

# ⚠️ 替换为你的真实 API Key
# 设置权限（仅当前用户可读）
chmod 600 .env
```

#### 2.5.4 创建 docker-compose.yml

在服务器上创建 `docker-compose.yml`（注意：阿里云镜像仓库地址需要替换）：

```bash
cat > docker-compose.yml << 'EOF'
services:
  enterprise-rag:
    image: registry.cn-hangzhou.aliyuncs.com/<命名空间>/enterprise-rag:latest
    container_name: enterprise-rag
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2"
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
EOF
```

> ⚠️ 请将 `registry.cn-hangzhou.aliyuncs.com/<命名空间>/enterprise-rag:latest` 替换为你的实际镜像地址。

#### 2.5.5 拉取并启动

```bash
# 拉取最新镜像
docker compose pull

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 查看容器状态
docker compose ps
```

#### 2.5.6 验证服务

```bash
# 测试 HTML 页面
curl -s http://localhost:8000/ | head -5

# 测试流式 API
curl -N http://localhost:8000/chat/stream?query=你好&department=测试部
```

---

### 2.6 配置 Nginx 反向代理与域名

#### 2.6.1 安装 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 2.6.2 创建 Nginx 配置

```bash
sudo vim /etc/nginx/sites-available/enterprise-rag
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或服务器 IP

    # 访问日志
    access_log /var/log/nginx/enterprise-rag-access.log;
    error_log  /var/log/nginx/enterprise-rag-error.log;

    # 客户端上传大小限制
    client_max_body_size 50m;

    # SSE 流式端点 —— 必须关闭缓冲
    location /chat/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 关键配置
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        chunked_transfer_encoding on;
    }

    # 其他请求（上传、静态资源）
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2.6.3 启用配置

```bash
# 创建符号链接启用站点
sudo ln -s /etc/nginx/sites-available/enterprise-rag /etc/nginx/sites-enabled/

# 删除默认站点
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置语法
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

#### 2.6.4 配置 HTTPS（可选，推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 为域名申请 SSL 证书
sudo certbot --nginx -d your-domain.com

# 证书会自动续期（已配置 systemd timer）
sudo systemctl status certbot.timer
```

---

### 2.7 验证与运维

#### 2.7.1 端到端测试

```bash
# 1. 上传文档测试
curl -X POST "http://your-domain.com/upload?department=技术部" \
  -F "file=@test_doc.txt"

# 期望响应：
# {"message":"test_doc.txt 已存入部门 [技术部] 知识库"}

# 2. 流式问答测试
curl -N "http://your-domain.com/chat/stream?query=文档主要内容是什么&department=技术部"

# 期望：流式输出回答文本，以 [DONE] 结束
```

#### 2.7.2 日常运维命令

```bash
# 查看服务状态
sudo systemctl status nginx
docker compose ps

# 查看日志
docker compose logs -f            # 实时日志
docker compose logs --tail=100    # 最近 100 行

# 重启服务
docker compose restart

# 更新镜像并重新部署
docker compose pull               # 拉取最新镜像
docker compose up -d              # 重新创建容器
docker image prune -f             # 清理旧镜像

# 备份数据
sudo tar -czf rag-backup-$(date +%Y%m%d).tar.gz /opt/enterprise-rag/data/
```

#### 2.7.3 监控与健康检查

```bash
# 手动触发健康检查
curl -f http://localhost:8000/ && echo "✓ 服务正常"

# 查看容器资源使用
docker stats enterprise-rag --no-stream

# 查看磁盘使用
df -h /opt/enterprise-rag/data/
```

#### 2.7.4 自动更新脚本

创建 `/opt/enterprise-rag/update.sh`：

```bash
#!/bin/bash
set -e

cd /opt/enterprise-rag

echo "[1/3] 拉取最新镜像..."
docker compose pull

echo "[2/3] 重启服务..."
docker compose up -d

echo "[3/3] 清理旧镜像..."
docker image prune -f

echo "✅ 更新完成"
docker compose ps
```

```bash
chmod +x /opt/enterprise-rag/update.sh
```

---

## 附录

### A. 快速参考卡片

```bash
# === 本地开发 ===
uv run uvicorn backend.app:app --reload          # 启动开发服务器
uv sync                                          # 安装/更新依赖

# === Git 操作 ===
git add . && git commit -m "feat: xxx"            # 提交
git push                                          # 推送
git pull                                          # 拉取

# === Docker 本地 ===
docker build -t enterprise-rag:latest .           # 构建
docker compose up -d                              # 启动
docker compose logs -f                            # 日志
docker compose down                               # 停止

# === 阿里云镜像推送 ===
docker tag enterprise-rag:latest registry.cn-hangzhou.aliyuncs.com/<ns>/enterprise-rag:latest
docker push registry.cn-hangzhou.aliyuncs.com/<ns>/enterprise-rag:latest

# === 服务器部署 ===
docker compose pull                               # 拉取
docker compose up -d                              # 启动
docker compose restart                            # 重启
```

### B. 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 容器启动后立即退出 | `.env` 未配置 API Key | 检查 `docker compose logs`，确保 `.env` 存在且有效 |
| 流式输出中断 | Nginx 未关闭缓冲 | 检查 `/chat/stream` location 中 `proxy_buffering off` |
| 上传大文件失败 | Nginx `client_max_body_size` 太小 | 增大到 `50m` |
| 模型下载失败 | 网络不通 | 配置 ModelScope 代理或提前下载模型挂载 |
| 端口被占用 | 其他服务占用 8000 | `sudo lsof -i :8000` 查看并调整 |
| 拉取镜像 401 | 未登录阿里云仓库 | `docker login` 重新认证 |

### C. 服务器资源分配参考

| 并发用户 | CPU | 内存 | 说明 |
|---------|-----|------|------|
| 1-5 | 2 核 | 4 GB | 最低配置 |
| 5-20 | 4 核 | 8 GB | 推荐配置 |
| 20-50 | 8 核 | 16 GB | 高并发 |
| 50+ | 考虑水平扩展 | — | 配合负载均衡 |
