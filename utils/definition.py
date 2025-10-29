import json
from typing import List
from loguru import logger as log
from database import CustomDocument, DocumentRecord
from model import TermDefinition
from utils.llm import llm_query


def extract_term_definition(
    term: str,
    docs: List[DocumentRecord],
) -> TermDefinition | None:
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
    if not len(docs):
        log.warning("No documents provided for term definition extraction.")
        return None

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
    1. 如果能在文档中找到定义
    "documents"字段请回复最主要的文档的标题。
    "page"字段请回复依据的页码。
    2. 如果文档中没有找到定义
    "documents"字段请回复空字符串。
    "page"字段请回复0。
"""

    # print(message)

    data = llm_query(message)
    result = json.loads(data)
    tr = TermDefinition(
        term=term,
        definition=result.get("definition", ""),
        reason=result.get("reason", ""),
        documents=result.get("documents", ""),
        page=result.get("page", 0),
    )

    return tr
