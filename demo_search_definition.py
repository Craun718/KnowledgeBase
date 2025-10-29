import json
from typing import List
from loguru import logger as log
from database import CustomDocument, DocumentRecord, similarity_search
from utils.llm import llm_query


word = "海洋灾害应急"


class TermDefinition:
    def __init__(self, term: str, definition: str, documents: str, page: int):
        self.term = term
        self.definition = definition
        self.documents = documents
        self.page = page


def extract_docs_has_single_term(term: str) -> List[DocumentRecord]:
    """Extract sentences containing the term from the text."""
    documents = similarity_search(f"包含{term}的句子", limit=10)

    results: List[DocumentRecord] = []
    for doc in documents:
        if term in doc.content:
            results.append(doc)

    print("Retrieved Documents:")
    print(f"Found {len(results)} documents containing the term.")

    return results


def extract_term_definition(
    term: str,
    docs: List[DocumentRecord],
) -> TermDefinition:
    """
    提取术语的定义

    参数:
        term: 需要查询的术语
        docs: 包含两个术语的文档（作为上下文）

    返回:
        TermDefinition 对象，包含术语定义信息
        {
            "term": <string>,
            "definition": <string>,
            "documents": <string>,
            "page": <number>
        }
    """
    # 1. 处理上下文：拼接文档内容作为分析依据
    log.debug(f"用于关系分析的上下文文档数：{len(docs)}")
    log.debug(json.dumps(docs[0].metadata, ensure_ascii=False, indent=2))

    context_docs = [
        CustomDocument(
            content=doc.content,
            doc_name=doc.metadata.get("source", "未知文档"),
            page_number=doc.metadata.get("page", 0),
        )
        for doc in docs
    ]

    source_docs = [
        f'{{"content": "{doc.content}", "doc_name": "{doc.doc_name}", "page_number": {doc.page_number}}}'
        for doc in context_docs
    ]

    context = "\n\n".join(source_docs)

    message = f"""
    # 根据以下上下文，请分析术语“{term}”的定义，并按要求回答。
    
    上下文内容如下：
    {context}
    
    # 回答格式
    请按照以下格式进行回答:
    {{
        "term": <string>,
        "definition": <string>,
        "documents": <string>,
        "page": <number>
    }}

    # 回答的要求:
    "definition"字段请直接回复术语的定义。
    "documents"字段请回复依据的文档标题。
    "page"字段请回复依据的页码。
"""

    # print(message)

    data = llm_query(message)
    result = json.loads(data)
    tr = TermDefinition(
        term=term,
        definition=result.get("definition", ""),
        documents=result.get("documents", ""),
        page=result.get("page", 0),
    )

    return tr


if __name__ == "__main__":
    docs = extract_docs_has_single_term(word)
    extract_term_definition(word, docs)
