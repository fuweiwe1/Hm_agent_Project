from typing import Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from model.factory import chat_model
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


class RagSummarizeService:
    def __init__(self):
        self.vector_store: Optional[VectorStoreService] = None
        self.retriever = None
        self.prompt_text: Optional[str] = None
        self.prompt_template: Optional[PromptTemplate] = None
        self.model = chat_model
        self.chain = None

    def _ensure_initialized(self) -> None:
        if self.chain is not None and self.retriever is not None:
            return

        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.chain = self.prompt_template | print_prompt | self.model | StrOutputParser()

    def retriever_docs(self, query: str) -> list[Document]:
        self._ensure_initialized()
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        self._ensure_initialized()

        context_docs = self.retriever_docs(query)
        context_lines = []
        for index, doc in enumerate(context_docs, start=1):
            context_lines.append(
                f"【参考资料{index}】 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}"
            )

        return self.chain.invoke(
            {
                "input": query,
                "context": "\n".join(context_lines),
            }
        )


if __name__ == "__main__":
    rag = RagSummarizeService()
    print(rag.rag_summarize("小户型适合哪些扫地机器人"))
