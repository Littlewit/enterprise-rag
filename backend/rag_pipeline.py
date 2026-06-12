"""知识库问答管道：文档加载、分块、向量化与多租户检索（Chroma）"""

import hashlib
import logging
import re
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.document_loaders import BaseLoader
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import (
    CHROMA_COLLECTION_PREFIX,
    CHROMA_PERSIST_DIR,
    CHUNK_OVERLAP,
    CHUNK_SEPARATORS,
    CHUNK_SIZE,
    RETRIEVER_TOP_K,
)
from .models import get_embeddings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """多租户知识库问答管道 —— 每个部门一个独立 Chroma Collection"""

    def __init__(self) -> None:
        self.embeddings: Embeddings = get_embeddings()
        # 持久化客户端，自动创建目录
        self._chroma_client: ClientAPI = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
        )
        # 缓存已创建的 langchain_chroma.Chroma 实例，避免重复初始化
        self._vectorstores: dict[str, Chroma] = {}
        logger.info("Chroma PersistentClient 已初始化: %s", CHROMA_PERSIST_DIR)

    _COLLECTION_NAME_SAFE_RE: re.Pattern[str] = re.compile(r"[^a-zA-Z0-9._-]")

    def _collection_name(self, department: str) -> str:
        """生成部门对应的 Collection 名称（自动 sanitize 非 ASCII 字符）"""
        # Chroma 要求 Collection 名仅含 [a-zA-Z0-9._-]，3-512 字符，首尾为字母数字
        safe = self._COLLECTION_NAME_SAFE_RE.sub("", department)
        if safe and len(safe) >= 3 and safe[0].isalnum() and safe[-1].isalnum():
            return f"{CHROMA_COLLECTION_PREFIX}{safe}"
        # 含中文等非 ASCII 字符时，用 SHA256 哈希前 12 位作为唯一标识
        hash_suffix = hashlib.sha256(department.encode()).hexdigest()[:12]
        return f"{CHROMA_COLLECTION_PREFIX}{hash_suffix}"

    @staticmethod
    def _get_loader(file_path: str) -> BaseLoader:
        """根据文件扩展名选择对应的轻量级加载器"""
        suffix = Path(file_path).suffix.lower()
        if suffix in (".txt", ".md"):
            return TextLoader(file_path, encoding="utf-8")
        if suffix == ".pdf":
            return PyPDFLoader(file_path)
        if suffix == ".docx":
            return Docx2txtLoader(file_path)
        if suffix == ".csv":
            return CSVLoader(file_path)
        raise ValueError(f"不支持的文件类型: {suffix}")

    def _get_or_create_vectorstore(self, department: str) -> Chroma:
        """按部门获取或创建 Chroma 向量库（带缓存）"""
        col_name = self._collection_name(department)
        if col_name not in self._vectorstores:
            # 确保底层 collection 存在
            _ = self._chroma_client.get_or_create_collection(name=col_name)
            self._vectorstores[col_name] = Chroma(
                client=self._chroma_client,
                collection_name=col_name,
                embedding_function=self.embeddings,
            )
            logger.info("已创建/加载 Collection: %s", col_name)
        return self._vectorstores[col_name]

    def process_document(self, file_path: str, department: str) -> None:
        """加载文档、分块并存入指定部门的向量库"""
        try:
            loader = self._get_loader(file_path)
            docs = loader.load()
        except Exception as e:
            logger.exception("文档加载失败: %s", file_path)
            raise RuntimeError(f"文档加载失败: {e}") from e

        if not docs:
            raise ValueError(f"文档内容为空: {file_path}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=CHUNK_SEPARATORS,
        )
        chunks = splitter.split_documents(docs)

        col_name = self._collection_name(department)
        # 清除该部门缓存的 VectorStore（因为新增了文档，需重建 retriever）
        _ = self._vectorstores.pop(col_name, None)

        # 直接向底层 collection 添加文档（langchain_chroma.Chroma 会处理向量化）
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            client=self._chroma_client,
            collection_name=col_name,
        )
        self._vectorstores[col_name] = vectorstore

        logger.info(
            "文档已存入部门 [%s]: %s (%d 个文本块)", department, file_path, len(chunks)
        )

    def get_retriever(self, department: str):
        """获取指定部门的向量检索器"""
        vectorstore = self._get_or_create_vectorstore(department)
        # 检查 Collection 中是否有数据
        col = self._chroma_client.get_collection(name=self._collection_name(department))
        if col.count() == 0:
            raise ValueError(f"部门 [{department}] 知识库为空，请先上传文档")
        return vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})
