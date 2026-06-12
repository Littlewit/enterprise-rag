"""LangGraph 工作流：检索 + 生成"""

import logging
from typing import Any  # noqa: UP035

from langchain_core.language_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever
from langgraph.graph import StateGraph, END  # pyright: ignore[reportMissingTypeStubs]
from typing_extensions import TypedDict

from .config import RAG_PROMPT_TEMPLATE
from .models import get_qwen_llm

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    query: str      # 查询内容
    context: str    # 检索到的上下文
    response: str   # 生成的回答


class RAGGraph:
    """RAG 工作流图：检索上下文 → LLM 生成回答"""

    retriever: BaseRetriever
    llm: BaseChatModel
    graph: Any  # pyright: ignore[reportExplicitAny]

    def __init__(self, retriever: BaseRetriever) -> None:
        self.retriever = retriever
        self.llm = get_qwen_llm()
        self.graph = self._build_graph()

    def _retrieve(self, state: AgentState) -> dict[str, str]:
        """检索相关文档上下文"""
        docs = self.retriever.invoke(state["query"])
        context = "\n\n".join(doc.page_content for doc in docs)  # type: ignore[attr-defined]
        return {"context": context}

    def _generate(self, state: AgentState) -> dict[str, str]:
        """基于上下文生成回答"""
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=state["context"], query=state["query"]
        )
        response = self.llm.invoke(prompt)
        return {"response": str(response.content)}

    def _build_graph(self) -> Any:  # pyright: ignore[reportExplicitAny]
        """构建工作流图：检索 → 生成 → 结束"""
        workflow = StateGraph(AgentState)
        _ = workflow.add_node("retrieve", self._retrieve)  # pyright: ignore[reportUnknownMemberType]
        _ = workflow.add_node("generate", self._generate)  # pyright: ignore[reportUnknownMemberType]

        _ = workflow.set_entry_point("retrieve")
        _ = workflow.add_edge("retrieve", "generate")
        _ = workflow.add_edge("generate", END)

        return workflow.compile()  # pyright: ignore[reportUnknownMemberType]

    def run(self, query: str) -> AgentState:
        """执行工作流并返回结果状态"""
        initial_state = AgentState(query=query, context="", response="")
        return self.graph.invoke(initial_state)  # type: ignore[no-any-return]
