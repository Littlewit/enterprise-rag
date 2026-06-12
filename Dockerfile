# ===== 构建阶段 =====
FROM python:3.13-slim AS builder

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先复制依赖声明文件，利用 Docker 缓存层
COPY pyproject.toml uv.lock ./

# 安装依赖到虚拟环境
RUN uv sync --frozen --no-dev --no-install-project

# ===== 运行阶段 =====
FROM python:3.13-slim AS runtime

WORKDIR /app

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY backend/ ./backend/
COPY main.py ./

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/data /app/models \
    && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
