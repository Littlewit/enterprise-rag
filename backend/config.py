"""集中管理所有配置常量"""

import os
from pathlib import Path

# ===== 路径配置 =====
# 项目根目录（backend/config.py 的上两级：enterprise-rag/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 当前模块所在目录（backend/）
BACKEND_DIR = Path(__file__).resolve().parent

# ===== LLM 配置（阿里千问） =====
LLM_MODEL_NAME = "qwen3.6-flash"
LLM_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_STREAMING = True # 开启流式输出
LLM_ENABLE_THINKING = False  # 关闭思考过程以减少输出

def get_llm_api_key() -> str:
    """惰性读取 API Key，确保 load_dotenv() 已先执行"""
    return os.getenv("DASHSCOPE_API_KEY", "")

# ===== Embedding 模型配置 =====
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
# 模型本地存储路径（相对于项目根目录）
EMBEDDING_LOCAL_DIR = str(PROJECT_ROOT / "models" / "bge-small-zh")
EMBEDDING_DEVICE = "cpu"
EMBEDDING_NORMALIZE = True # 是否对向量进行归一化

# ===== 文档处理配置 =====
CHUNK_SIZE = 500 # 文本块大小（字符数）
CHUNK_OVERLAP = 50 # 文本块重叠大小（字符数）
CHUNK_SEPARATORS = ["\n\n", "\n", "。", "！", "？", " ", ""] # 文本块分隔符

# ===== 检索配置 =====
RETRIEVER_TOP_K = 3 # 检索结果数量

# ===== Prompt 模板 =====
RAG_PROMPT_TEMPLATE = "基于以下信息回答问题：\n{context}\n\n问题：{query}"

# ===== 文件上传校验 =====
# 允许上传的文件扩展名
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".csv"}
# 最大上传文件大小（字节）
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

# ===== Chroma 向量库配置 =====
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "data" / "chroma")
CHROMA_COLLECTION_PREFIX = "dept_"  # Collection 命名前缀

# ===== 部门名校验 =====
import re
DEPT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fff]{1,32}$")  # 允许中英文/数字/下划线，1-32字符
DEPT_NAME_MAX_LENGTH = 32

# ===== 输入校验 =====
MAX_QUERY_LENGTH = 2000 # 最大查询长度
MIN_QUERY_LENGTH = 1 # 最小查询长度
