"""FastAPI 接口层：文档上传、流式问答、多租户隔离"""

import asyncio
import logging
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    BACKEND_DIR,
    DEPT_NAME_MAX_LENGTH,
    DEPT_NAME_PATTERN,
    MAX_QUERY_LENGTH,
    MAX_UPLOAD_SIZE_BYTES,
    MIN_QUERY_LENGTH,
    RAG_PROMPT_TEMPLATE,
)
from .graph_workflow import RAGGraph
from .rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

app = FastAPI(title="企业级知识库问答系统")

# 惰性初始化：首次请求时才加载模型
_rag_pipeline: RAGPipeline | None = None


def _get_pipeline() -> RAGPipeline:
    """获取 RAGPipeline 单例（惰性初始化）"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        logger.info("RAGPipeline 已初始化")
    return _rag_pipeline


def _validate_department(department: str) -> None:
    """校验部门名称"""
    if not department or not department.strip():
        raise HTTPException(status_code=400, detail="部门名称不能为空")
    department = department.strip()
    if len(department) > DEPT_NAME_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"部门名称长度 {len(department)} 超过限制 {DEPT_NAME_MAX_LENGTH}",
        )
    if not DEPT_NAME_PATTERN.match(department):
        raise HTTPException(
            status_code=400,
            detail="部门名称只允许中英文、数字和下划线，长度1-32字符",
        )


def _validate_upload_file(file: UploadFile) -> None:
    """校验上传文件类型和大小"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {suffix}，允许的类型: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    if file.size is not None and file.size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小 {file.size} 超过限制 {MAX_UPLOAD_SIZE_BYTES} 字节",
        )


def _validate_query(query: str) -> None:
    """校验查询参数"""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"查询长度 {len(query)} 超过限制 {MAX_QUERY_LENGTH}",
        )
    if len(query.strip()) < MIN_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="查询内容过短")


@app.post("/upload")
async def upload_document(
    department: str = Query(..., description="部门名称"),
    file: UploadFile = File(...),  # pyright: ignore[reportCallInDefaultInitializer]
) -> dict[str, str]:
    """上传文档并解析入库到指定部门"""
    _validate_department(department)
    department = department.strip()
    _validate_upload_file(file)
    assert file.filename is not None  # 校验后保证非空

    # 将上传文件保存到临时目录
    content = await file.read()
    with tempfile.NamedTemporaryFile(
        suffix=Path(file.filename).suffix, delete=False
    ) as tmp:
        _ = tmp.write(content)
        tmp_path = tmp.name

    try:
        pipeline = _get_pipeline()
        # 异步执行同步的文档处理，避免阻塞事件循环
        await asyncio.to_thread(pipeline.process_document, tmp_path, department)
        logger.info("文档已入库 [%s]: %s", department, file.filename)
    except Exception as e:
        logger.exception("文档处理失败: %s", e)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}") from e
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

    return {"message": f"{file.filename} 已存入部门 [{department}] 知识库"}


@app.get("/chat/stream")
async def stream_chat(
    query: str = Query(..., description="问题内容"),
    department: str = Query(..., description="部门名称"),
) -> StreamingResponse:
    """流式问答接口（GET 兼容 EventSource）"""
    _validate_query(query)
    _validate_department(department)
    department = department.strip()

    pipeline = _get_pipeline()
    retriever = pipeline.get_retriever(department)
    rag_graph = RAGGraph(retriever)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 1. 执行检索工作流
            state = await asyncio.to_thread(rag_graph.run, query)
            context = state["context"]

            # 2. 流式输出 LLM 结果（复用 graph 的 LLM，不重新创建）
            llm = rag_graph.llm
            prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=query)

            for chunk in llm.stream(prompt):
                yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("流式问答异常: %s", e)
            yield f"data: [ERROR] {e}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ===== 挂载静态前端页面 =====
# 确保 static 目录存在
static_dir = Path(BACKEND_DIR, "static")
static_dir.mkdir(exist_ok=True)

app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
