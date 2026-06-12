"""LLM 与 Embedding 模型管理模块，提供惰性单例缓存"""

import logging
import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from modelscope import snapshot_download  # pyright: ignore[reportMissingTypeStubs,reportUnknownVariableType]
from pydantic import SecretStr

from .config import (
    EMBEDDING_DEVICE,
    EMBEDDING_LOCAL_DIR,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_NORMALIZE,
    LLM_BASE_URL,
    LLM_ENABLE_THINKING,
    LLM_MODEL_NAME,
    LLM_STREAMING,
    get_llm_api_key,
)

logger = logging.getLogger(__name__)

_ = load_dotenv()

# ===== 模块级惰性单例缓存 =====
_llm_instance: ChatOpenAI | None = None # 阿里千问 LLM 实例
_embedding_instance: HuggingFaceEmbeddings | None = None # 百度嵌入模型实例


def get_qwen_llm() -> ChatOpenAI:
    """获取阿里千问 LLM 实例（惰性单例）"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model=LLM_MODEL_NAME,
            api_key=SecretStr(get_llm_api_key()) if get_llm_api_key() else None,
            base_url=LLM_BASE_URL,
            streaming=LLM_STREAMING,
            extra_body={"enable_thinking": LLM_ENABLE_THINKING},
        )
        logger.info("LLM 实例已创建: %s", LLM_MODEL_NAME)
    return _llm_instance


def get_embeddings() -> HuggingFaceEmbeddings:
    """获取百度嵌入模型实例（惰性单例，自动下载到本地）"""
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    # 检查模型是否已下载
    if not os.path.exists(os.path.join(EMBEDDING_LOCAL_DIR, "config.json")):
        logger.info("正在从魔搭社区下载模型 %s ...", EMBEDDING_MODEL_NAME)
        try:
            _ = snapshot_download(EMBEDDING_MODEL_NAME, local_dir=EMBEDDING_LOCAL_DIR)
            logger.info("模型下载成功: %s", EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.error("模型下载失败: %s", e)
            raise RuntimeError(f"模型下载失败: {e}") from e
    else:
        logger.info("检测到本地已存在模型文件: %s", EMBEDDING_LOCAL_DIR)

    _embedding_instance = HuggingFaceEmbeddings(
        model_name=EMBEDDING_LOCAL_DIR,
        model_kwargs={"device": EMBEDDING_DEVICE},
        encode_kwargs={"normalize_embeddings": EMBEDDING_NORMALIZE},
    )
    logger.info("Embedding 模型已加载: %s", EMBEDDING_MODEL_NAME)
    return _embedding_instance
