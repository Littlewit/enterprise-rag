# =============================================================================
# GitHub 仓库初始化与首次推送脚本 (PowerShell)
# 使用前请先在 GitHub 上创建一个空仓库（不要勾选 README/.gitignore/LICENSE）
# =============================================================================

$ErrorActionPreference = "Stop"
$repoUrl = Read-Host -Prompt "请输入 GitHub 仓库 URL（如 https://github.com/user/enterprise-rag.git）"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Enterprise-RAG GitHub 仓库初始化与推送" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. 初始化 Git（如需要）
if (-not (Test-Path ".git")) {
    Write-Host "[1/4] 初始化 Git 仓库..." -ForegroundColor Yellow
    git init
} else {
    Write-Host "[1/4] Git 仓库已存在，跳过初始化" -ForegroundColor Green
}

# 2. 添加并提交
Write-Host "[2/4] 添加文件并创建初始提交..." -ForegroundColor Yellow
git add .
git status

$confirm = Read-Host -Prompt "确认提交？(y/n)"
if ($confirm -eq "y") {
    git commit -m "chore: init enterprise-rag project

- 基于 FastAPI + LangChain + Chroma 的多租户 RAG 知识库问答系统
- 支持多部门文档隔离上传与流式 AI 问答
- Docker 容器化部署支持"
} else {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# 3. 添加远程仓库
Write-Host "[3/4] 添加远程仓库..." -ForegroundColor Yellow
git remote add origin $repoUrl 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "远程仓库已存在，更新 URL..." -ForegroundColor Yellow
    git remote set-url origin $repoUrl
}
Write-Host "远程仓库: $repoUrl" -ForegroundColor Green

# 4. 推送
Write-Host "[4/4] 推送到 GitHub..." -ForegroundColor Yellow
git push -u origin master

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  推送完成！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "--- 后续日常提交流程 ---" -ForegroundColor Gray
Write-Host "  git add ."
Write-Host "  git commit -m 'feat: 描述你的修改'"
Write-Host "  git push"
Write-Host ""
Write-Host "--- 提交信息规范 ---" -ForegroundColor Gray
Write-Host "  feat:     新功能"
Write-Host "  fix:      Bug 修复"
Write-Host "  docs:     文档更新"
Write-Host "  refactor: 代码重构"
Write-Host "  chore:    构建/工具变更"
