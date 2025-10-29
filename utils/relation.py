from model import TermRelation
import json
from typing import List

from loguru import logger as log

from database import CustomDocument, DocumentRecord, similarity_search
from utils.llm import llm_query


def extract_term_relation(
    term1: str,
    term2: str,
    docs: List[DocumentRecord],
) -> TermRelation | None:
    """
    提取两个术语的关系

    参数:
        term1: 第一个术语
        term2: 第二个术语
        docs: 包含两个术语的文档（作为上下文）

    返回:
        TermRelation 对象，包含术语关系信息
        {
            "relationship": <number>,
            "documents": <string>,
            "page": <number>
        }
        "relationship"的内容要求如下：
        1. 如果为因果关系，回复`1`；
        2. 如果为主从关系，回复`2`；
    """
    # 1. 处理上下文：拼接文档内容作为分析依据
    if not len(docs):
        log.warning("No documents provided for term relation extraction.")
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

    log.debug(f"文档上下文数量：{len(context_docs)}")
    log.debug(json.dumps(context_docs[0].to_dict(), ensure_ascii=False, indent=2))

    source_docs = [
        f'{{"content": "{doc.content}", "doc_name": "{doc.doc_name}", "page_number": {doc.page_number}}}'
        for doc in context_docs
    ]

    context = "\n\n".join(source_docs)
    # log.debug(f"用于关系分析的上下文文档：{context}")

    message = f"""
    # 根据以下上下文，请分析术语“{term1}”和“{term2}”之间的关系，并按要求回答。
    
    上下文内容如下：
    {context}
    
    请按照以下格式进行回答:
    {{
        "relationship": <number>,
        "reason": <string>,
        "documents": <string>,
        "page": <number>
    }}

    "relationship"的内容要求如下：
    1. 如果为因果关系，回复`1`；
    2. 如果为主从关系，回复`2`；
    
    "reason"字段的内容要求如下：
    1. 请在"reason"中填入引入文档的原文解释

    "documents"的内容要求如下：
    1. 请在"documents"中填入引入文档的标题；

    "page"的内容要求如下：
    1. 请在"page"中填入引入文档的页码；
"""

    # print(message)

    data = llm_query(message)
    result = json.loads(data)

    relation = result.get("relationship", 0)
    if type(relation) == str:
        relationNumber = int(relation)
    elif type(relation) == int:
        relationNumber = relation
    else:
        relationNumber = 0

    if relationNumber == 0:
        relationStr = "没有关系"
    elif relationNumber == 1:
        relationStr = "因果关系"
    elif relationNumber == 2:
        relationStr = "主从关系"
    else:
        relationStr = "没有关系"

    tr = TermRelation(
        term1=term1,
        term2=term2,
        relation=relationStr,
        reason=result.get("reason", ""),
        documents=result.get("documents", "").replace(".pdf", "").replace("/T", "_T_"),
        page=result.get("page", 0),
    )

    return tr
