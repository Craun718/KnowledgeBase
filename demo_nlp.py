import json
from typing import Dict, List
import spacy
from pathlib import Path

from loguru import logger as log

from config import self_dir
from database import CustomDocument, DocumentRecord, similarity_search
from utils.llm import llm_query


class TermRelation:
    def __init__(
        self, term1: str, term2: str, relation: str, documents: str, page: int
    ):
        self.term1 = term1
        self.term2 = term2
        self.relation = relation
        self.documents = documents
        self.page = page


model_dir = (
    Path(self_dir)
    / "models"
    / "zh_core_web_lg-3.8.0"
    / "zh_core_web_lg"
    / "zh_core_web_lg-3.8.0"
)

nlp = spacy.load(model_dir)

target_term_pair = ("海洋灾害", "海洋灾害应急")


def extract_docs_has_terms(term_pair: tuple) -> List[DocumentRecord]:
    """Extract sentences containing both terms from the text."""
    documents = similarity_search(
        f"同时包含{term_pair[0]}和{term_pair[1]}的句子", limit=10
    )

    results: List[DocumentRecord] = []
    for doc in documents:
        if target_term_pair[0] in doc.content and target_term_pair[1] in doc.content:
            results.append(doc)

    print("Retrieved Documents:")
    print(f"Found {len(results)} documents containing both terms.")
    for doc in results:
        print("--------------------")
        print(f"{doc.content}...")  # 打印前100个字符预览

    return results


def extract_term_relation(
    term1: str,
    term2: str,
    docs: List[DocumentRecord],
) -> TermRelation:
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
        2. 如果为从属关系，回复`2`；
        3. 不属于这两种关系，回复`0`。
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
        "documents": <string>,
        "page": <number>
    }}

    "relationship"的内容要求如下：
    1. 如果为因果关系，回复`1`；
    2. 如果为从属关系，回复`2`；
    3. 不属于这两种关系，回复`0`。
    
    "reason"字段的内容要求如下：
    1. 如果关系为因果关系或从属关系，请在"documents"和"page"中说明依据的文档标题和页码；
    2. 如果关系为非因果非从属关系，请将"documents"和"page"设为空字符串和0。
"""

    # print(message)

    data = llm_query(message)
    result = json.loads(data)
    tr = TermRelation(
        term1=term1,
        term2=term2,
        relation=result.get("relationship", "0"),
        documents=result.get("documents", ""),
        page=result.get("page", 0),
    )

    return tr


if __name__ == "__main__":
    # 步骤1：获取包含两个术语的文档
    context_docs = extract_docs_has_terms(target_term_pair)
    print(f"用于分析的上下文文档数：{len(context_docs)}")

    # 步骤2：提取术语关系
    relation_result = extract_term_relation(
        term1=target_term_pair[0], term2=target_term_pair[1], docs=context_docs
    )
