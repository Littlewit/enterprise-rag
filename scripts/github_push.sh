#!/bin/bash
# =============================================================================
# GitHub 仓库初始化与首次推送脚本
# 使用前请先在 GitHub 上创建一个空仓库（不要勾选 README/.gitignore/LICENSE）
# =============================================================================

set -e  # 遇到错误立即退出

echo "============================================"
echo "  Enterprise-RAG GitHub 仓库初始化与推送"
echo "============================================"
echo ""

# ===== 配置（请修改为你的仓库信息）=====
GITHUB_USER="your-username"            # GitHub 用户名
REPO_NAME="enterprise-rag"             # 仓库名
BRANCH="master"                        # 主分支名（master 或 main）
# ======================================

# 1. 初始化 Git 仓库（如果尚未初始化）
if [ ! -d ".git" ]; then
    echo "[1/5] 初始化 Git 仓库..."
    git init
    git checkout -b ${BRANCH}
else
    echo "[1/5] Git 仓库已存在，跳过初始化"
    # 确保在正确的分支上
    git checkout ${BRANCH} 2>/dev/null || git checkout -b ${BRANCH}
fi

# 2. 配置用户信息（如未配置）
if [ -z "$(git config user.name)" ]; then
    echo "[2/5] 请先配置 Git 用户信息："
    echo "  git config user.name \"Your Name\""
    echo "  git config user.email \"your@email.com\""
    echo ""
    read -p "是否现在配置？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入用户名: " GIT_NAME
        read -p "请输入邮箱: " GIT_EMAIL
        git config user.name "$GIT_NAME"
        git config user.email "$GIT_EMAIL"
    else
        echo "请手动配置后重新运行此脚本"
        exit 1
    fi
else
    echo "[2/5] Git 用户: $(git config user.name) <$(git config user.email)>"
fi

# 3. 添加所有文件并提交
echo "[3/5] 添加文件并创建初始提交..."
git add .
git status

read -p "确认提交以上文件？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "chore: init enterprise-rag project

- 基于 FastAPI + LangChain + Chroma 的多租户 RAG 知识库问答系统
- 支持多部门文档隔离上传与流式 AI 问答
- Docker 容器化部署支持"
else
    echo "已取消"
    exit 0
fi

# 4. 添加远程仓库
echo "[4/5] 配置远程仓库..."
REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

if git remote get-url origin 2>/dev/null; then
    echo "远程仓库 origin 已存在: $(git remote get-url origin)"
    read -p "是否覆盖为 ${REMOTE_URL}？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin "$REMOTE_URL"
    fi
else
    git remote add origin "$REMOTE_URL"
    echo "已添加远程仓库: $REMOTE_URL"
fi

# 5. 推送到 GitHub
echo "[5/5] 推送到 GitHub..."
git push -u origin ${BRANCH}

echo ""
echo "============================================"
echo "  ✅ 推送完成！"
echo "  仓库地址: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "============================================"

# 后续日常提交流程提示
echo ""
echo "--- 后续日常提交流程 ---"
echo "  git add ."
echo "  git commit -m \"feat: 描述你的修改\""
echo "  git push"
echo ""
echo "--- 提交信息规范 ---"
echo "  feat:     新功能"
echo "  fix:      Bug 修复"
echo "  docs:     文档更新"
echo "  refactor: 代码重构"
echo "  chore:    构建/工具变更"
